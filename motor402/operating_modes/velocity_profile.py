from dataclasses import dataclass
from canopen import RemoteNode
from ..utility import *

@dataclass
class VelocityProfileAddresses:
    position_demand_value: int = 0x6062
    position_actual_internal_value: int = 0x6063
    position_actual_value: int = 0x6064
    following_error_window: int = 0x6065
    velocity_actual_value: int = 0x606C
    software_position_limit: int = 0x607D
    profile_acceleration: int = 0x6083
    quick_stop_deceleration: int = 0x6085
    target_velocity: int = 0x60FF

class VelocityProfile:

    def __init__(self, node: RemoteNode):
        self._node = node
        self.profile_code = 3
        self.addresses = VelocityProfileAddresses()

    def set_command(self, value):
        self.set_velocity(value)

    def set_velocity(self, velocity):
        """Set the profile velocity which is normally attained at
        the end of the acceleration ramp during a profiled move
        and is valid for both directions of motion.

        Args:
            velocity (int): target velocity, given in user defined speed units
        """
        self._node.sdo[self.addresses.target_velocity].raw = uint32(velocity)

    def set_quick_stop_deceleration(self, deceleration):
        """Set the maximum Quick Stop Deceleration.
        Limited by 60C6h (Max Deceleration) and, if applicable, 60A4h (Profile Jerk).

        Args:
            deceleration (int): max deceleration, given in user-defined units
        """
        self._node.sdo[self.addresses.quick_stop_deceleration].raw = uint32(deceleration)

    def get_velocity(self):
        """Current velocity

        Returns:
            int: current actual speed in user-defined units
        """
        return self._node.sdo[self.addresses.velocity_actual_value].raw
