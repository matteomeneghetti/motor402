from motor402 import *
from motor402.utility import *
import time
from signal import signal, SIGINT
import canopen
from math import sin, pi

rename_map = {
    "controlword": "Controlword 1",
    "statusword": "Statusword 1",
    "operating_mode": "Modes of Operation 1",
    "target_position": "Target Position 1",
    "profile_velocity": "Profile Velocity in pp-mode 1",
    "target_velocity": "Target Velocity 1",
    "homing_method": "Homing Method 1",
    "position_actual_value": "Position Actual Value 1",
    "velocity_actual_value": "Velocity Actual Value 1",
    "switches": "Switch Parameters 1",
    "microstep_resolution": "Microstep Resolution 1"
}

rename_map2 = {
    "controlword": "Controlword 2",
    "statusword": "Statusword 2",
    "operating_mode": "Modes of Operation 2",
    "target_position": "Target Position 2",
    "profile_velocity": "Profile Velocity in pp-mode 2",
    "target_velocity": "Target Velocity 2",
    "homing_method": "Homing Method 2",
    "position_actual_value": "Position Actual Value 2",
    "velocity_actual_value": "Velocity Actual Value 2",
    "switches": "Switch Parameters 2",
    "microstep_resolution": "Microstep Resolution 2"
}

rename_map3 = {
    "controlword": "Controlword 3",
    "statusword": "Statusword 3",
    "operating_mode": "Modes of Operation 3",
    "target_position": "Target Position 3",
    "profile_velocity": "Profile Velocity in pp-mode 3",
    "target_velocity": "Target Velocity 3",
    "homing_method": "Homing Method 3",
    "position_actual_value": "Position Actual Value 3",
    "velocity_actual_value": "Velocity Actual Value 3",
    "switches": "Switch Parameters 3",
    "microstep_resolution": "Microstep Resolution 3"
}

rename_map4 = {
    "controlword": "Controlword 4",
    "statusword": "Statusword 4",
    "operating_mode": "Modes of Operation 4",
    "target_position": "Target Position 4",
    "profile_velocity": "Profile Velocity in pp-mode 4",
    "target_velocity": "Target Velocity 4",
    "homing_method": "Homing Method 4",
    "position_actual_value": "Position Actual Value 4",
    "velocity_actual_value": "Velocity Actual Value 4",
    "switches": "Switch Parameters 4",
    "microstep_resolution": "Microstep Resolution 4"
}

motion_profiles_cfg = {
    "index": "operating_mode",
    "profiles": {
        "no_mode": 0,
        "pp": 1,
        "pv": 2,
        "hm": 6,
        "csp": 8,
        "csv": 9
    }
}

signal(SIGINT, lambda h, f: (motor.shutdown(), exit(0)))

network = canopen.Network()
node = canopen.RemoteNode(0x75, "./examples/TMCM-6212.eds")
network.add_node(node)
network.connect(bustype="socketcan", channel="can0", bitrate=1000000)
time.sleep(0.1)

node.nmt.state = "PRE-OPERATIONAL"
node.tpdo.read()
node.rpdo.read()

def generator_pos():
    start = time.time()
    while True:
        actual_time = time.time() - start
        if actual_time > 30:
            break
        value = 30*sin(2*pi*0.25*actual_time)
        value = value/0.0127*256
        yield(int(value),)

traj_rpdo = RPDOConfig(1, ("target_position",), data=generator_pos, frequency=1000, rtr_allowed=False)
status_tpdo = TPDOConfig(1, ("statusword",), rtr_allowed=False, event_timer=5)

motor = Motor(node, rename_map=rename_map, motion_profiles=motion_profiles_cfg)
motor.set_tpdos([status_tpdo])
node.nmt.state = "OPERATIONAL"
motor.to_switch_on_disabled()
motor.set("switches", uint32(3))
motor.set("profile_velocity", int32(30/0.0127*256))


motor.move_to_target(150/0.0127*256)
while not motor.get('statusword', property='bits', force_sdo=False)[14]: pass
while motor.get('statusword', property='bits', force_sdo=False)[14]:
    time.sleep(0.1)

motor.set_home_pos()

motor.follow_trajectory(traj_rpdo)
while not motor.get('statusword', property='bits', force_sdo=False)[14]: pass
while motor.get('statusword', property='bits', force_sdo=False)[14]: time.sleep(0.1)

motor.go_home()
while not motor.get('statusword', property='bits', force_sdo=False)[14]: pass
while motor.get('statusword', property='bits', force_sdo=False)[14]:
    time.sleep(0.1)

motor.move_to_target(-150/0.0127*256)
while not motor.get('statusword', property='bits', force_sdo=False)[14]: pass
while motor.get('statusword', property='bits', force_sdo=False)[14]:
    time.sleep(0.1)

motor.set_home_pos()
