import canopen
import math
import time
from math import sin, cos, degrees, radians
from motor402 import Motor
from motor402.utility import *
from motor402.operating_modes import PositionProfile
from dataclasses import fields

class TrinamicMotor(Motor):

    def __init__(self, board, id: int):
        super().__init__(board)
        self.id = id
        self.__micro_per_step = 256
        self.__full_step = 200

        self.attach(PositionProfile(board))
        # Offset all the operating mode addresses
        # Non-standard implementation of the CANopen protocol:
        # All motor axis > 0 have their object addressess offset by 0x800 * axis_number
        for field in fields(self.operatingMode.addresses):
            setattr(self.operatingMode.addresses, field.name, getattr(self.operatingMode.addresses, field.name) + 0x800 * id)

        self.addresses.controlword = 0x6040 + 0x800 * id
        self.addresses.statusword = 0x6041 + 0x800 * id
        self.addresses.operation_mode = 0x6060 + 0x800 * id
        self.addresses.microstep_resolution = 0x2000 + 0x200 * id
        self.addresses.fullstep_resolution = 0x2001 + 0x200 * id
        self.addresses.maximum_current = 0x2003 + 0x200 * id
        self.addresses.standby_current = 0x2004 + 0x200 * id
        self.addresses.switch_parameters = 0x2005 + 0x200 * id

    @property
    def switch_parameters(self):
        return self._node.sdo[self.addresses.switch_parameters].raw

    @switch_parameters.setter
    def switch_parameters(self, value):
        self._node.sdo[self.addresses.switch_parameters].raw = uint32(value)

    @property
    def microstep_resolution(self):
        return int(math.pow(2, self._node.sdo[self.addresses.microstep_resolution].raw))

    @microstep_resolution.setter
    def microstep_resolution(self, value):
        self.__micro_per_step = int(value)
        self._node.sdo[self.addresses.microstep_resolution].raw = uint8(int(math.log2(value)))

    @property
    def fullstep_resolution(self):
        return self._node.sdo[self.addresses.fullstep_resolution].raw

    @fullstep_resolution.setter
    def fullstep_resolution(self, value):
        self.__full_step = int(value)
        self._node.sdo[self.addresses.fullstep_resolution].raw = uint16(self.__full_step)

    @property
    def maximum_current(self):
        return self._node.sdo[self.addresses.maximum_current].raw

    @maximum_current.setter
    def maximum_current(self, value):
        value = int(value * 255)
        self._node.sdo[self.addresses.maximum_current].raw = uint8(value)

    @property
    def standby_current(self):
        return self._node.sdo[self.addresses.standby_current].raw

    @standby_current.setter
    def standby_current(self, value):
        value = int(value * 255)
        self._node.sdo[self.addresses.standby_current].raw = uint8(value)

    def move(self, steps):
        self._move(steps * self.__micro_per_step)

    def is_moving(self):
        return bool(self.statusword & 0x4000)


# PPRRP(R) robot
class BackRipper:

    def __init__(self, board_id, path_to_eds):
        self.network = canopen.Network()
        self.node = canopen.RemoteNode(board_id, path_to_eds)
        self.network.add_node(self.node)
        self.motors = {}
        self.limits = [
            (-150, 150), # mm
            (-85, 85), # mm
            (-45, 45), # deg
            (-20, 20), # deg
            (-60, 60) # mm
        ]

    def __len__(self):
        return len(self.motors)

    def __setitem__(self, motor_index, motor):
          self.motors[motor_index] = motor

    def __getitem__(self, motor_index):
          return self.motors[motor_index]

    def connect(self):
        try:
            self.network.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)
            return True
        except:
            return False

    def init(self):
        for i in range(5):
            motor = TrinamicMotor(self.node, i)
            self.motors[i] = motor
            motor._recover_from_fault()
            if motor.state == 'SWITCH ON DISABLED':
                if motor.operation_mode != motor.operatingMode.profile_code:
                    motor.operation_mode = motor.operatingMode.profile_code
                motor.switch_parameters = 3 # No limit switches
                motor.maximum_current = 0.6 # 60% of 1.1A
                self.motors[i].operatingMode.set_velocity(int(51200))
                min, max = self.limits[i]
                if i in (2,3):
                    min = min * 100 * 256
                    max = max * 100 * 256
                else:
                    min = min / 0.0127 * 256 - 1
                    max = max / 0.0127 * 256 + 1
                self.motors[i].operatingMode.set_software_position_limit(int(min), int(max))
        self.node.nmt.state = 'OPERATIONAL'

    def ikine(self, position, orientation):
        """
            position: mm
            orientation: rad
        """

        x, y, z = position
        phi, theta = orientation
        ee_w = 87.5 + 60 # end effector offset relative to wrist center (mm) + home Z
        q5 =  (z - ee_w*cos(phi)*cos(theta) + ee_w) / (cos(phi)*cos(theta))
        q1 = y + (ee_w+q5)*cos(theta)*sin(phi)
        q2 = x - (ee_w+q5)*sin(theta)
        q3 = -phi
        q4 = -theta
        return [q1, q2, degrees(q3), degrees(q4), q5]

    def move(self, targets: list):
        for motor_id, motor in self.motors.items():
            motor._recover_from_fault()
            if motor_id == 4:
                continue
            target = targets[motor_id]
            target = sorted([target, self.limits[motor_id][0], self.limits[motor_id][1]])[1]
            if motor_id in (2,3):
                motor.move(100 * target)
            else:
                motor.move(target / 0.0127)

if __name__ == "__main__":
    robot = BackRipper(0x75, './TMCM-6212.eds')
    if not robot.connect():
        print("Unable to connect to the board")
        exit(-1)
    robot.init()
    # 10,-35,50
    # 50,-35,13
    q = robot.ikine((0,0,0), (radians(0), radians(0)))
    print(q)
    robot[4].move(-60/0.0127)
    while robot[4].is_moving():
        time.sleep(0.2)
    robot.move(q)
    while robot[0].is_moving() or robot[1].is_moving() or robot[2].is_moving() or robot[3].is_moving():
        time.sleep(0.2)
    robot[4].move(q[4]/0.0127)
    while robot[4].is_moving():
        time.sleep(0.2)
