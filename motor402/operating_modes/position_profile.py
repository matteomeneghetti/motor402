from dataclasses import dataclass
from canopen import RemoteNode
from abc import ABC, abstractmethod
from ..utility import *
from .operating_mode import OperatingMode

@dataclass
class PositionProfileAddresses:
    position_demand_value: int = 0x6062
    position_actual_internal_value: int = 0x6063
    position_actual_value: int = 0x6064
    following_error_window: int = 0x6065
    position_window: int = 0x6067
    position_window_time: int = 0x6068
    velocity_actual_value: int = 0x606C
    target_position: int = 0x607A
    software_position_limit: int = 0x607D
    profile_velocity: int = 0x6081
    end_velocity: int = 0x6082
    profile_acceleration: int = 0x6083
    profile_deceleration: int = 0x6084
    quick_stop_deceleration: int = 0x6085
    positioning_option_code: int = 0x60F2

class PositionProfileStatus:

    def __init__(self):
        pass

class PositionProfile(OperatingMode):

    def __init__(self, node: RemoteNode):
        self._node = node
        self.profile_code = 1
        self.addresses = PositionProfileAddresses()

    def set_command(self, position):
        """Execute the default profile command (set position)

        Args:
            position (int): target position, given in user defined position units
        """
        self.set_position(position)

    def set_position(self, position):
        """Set the position that the drive should move to using
        the current settings of motion control parameters
        such as velocity, acceleration and deceleration

        Args:
            position (int): target position, given in user defined position units
        """
        self._node.sdo.download(self.addresses.target_position, 0, int32(int(position)))

    def set_velocity(self, velocity):
        """Set the profile velocity which is normally attained at
        the end of the acceleration ramp during a profiled move
        and is valid for both directions of motion.

        Args:
            velocity (int): target velocity, given in user defined speed units
        """
        self._node.sdo[self.addresses.profile_velocity].raw = uint32(velocity)

    def set_acceleration(self, acceleration):
        """Set the desired starting acceleration used during the acceleration ramp.

        Args:
            acceleration (int): target acceleration, given in user defined acceleration units
        """
        self._node.sdo[self.addresses.profile_acceleration].raw = uint32(acceleration)

    def set_deceleration(self, deceleration):
        """Set the desired braking deceleration used during the deceleration ramp.
        If this parameter is not supported, then the profile acceleration value is also used for deceleration.

        Args:
            acceleration (int): target deceleration, given in the same units as the profile acceleration
        """
        self._node.sdo[self.addresses.profile_deceleration].raw = uint32(deceleration)

    def set_quick_stop_deceleration(self, deceleration):
        """Set the maximum Quick Stop Deceleration.
        Limited by 60C6h (Max Deceleration) and, if applicable, 60A4h (Profile Jerk).

        Args:
            deceleration (int): max deceleration, given in user-defined units
        """
        self._node.sdo[self.addresses.quick_stop_deceleration].raw = uint32(deceleration)

    def set_position_window(self, window):
        """This object defines a symmetrical range of accepted positions relative to the target
        position. If the actual value of the position encoder is within the position window, this target
        position is regarded as reached.

        Args:
            window (int): position window, specified in user-defined units
        """
        self._node.sdo[self.addresses.position_window].raw = uint32(window)

    def set_position_window_time(self, time):
        """Minimum residence time within the corridor in Position Profile operating mode,
        until the target position is reported as achieved.

        Args:
            time (int): time range, given in milliseconds
        """
        self._node.sdo[self.addresses.position_window_time].raw = uint16(time)

    def set_software_position_limit(self, min, max):
        """Defines the limit positions relative to the reference point of the application

        Args:
            min (int): min position limit, given in user-defined units
            max (int): max position limit, given in user-defined units
        """
        self._node.sdo.download(self.addresses.software_position_limit, 1, int32(min))
        self._node.sdo.download(self.addresses.software_position_limit, 2, int32(max))

    def get_position(self):
        return self._node.sdo[self.addresses.position_actual_value].raw

    def get_velocity(self):
        return self._node.sdo[self.addresses.velocity_actual_value].raw

if __name__ == "__main__":
    print(help(PositionProfile))