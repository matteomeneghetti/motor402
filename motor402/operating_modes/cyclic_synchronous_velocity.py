from dataclasses import dataclass
from canopen import RemoteNode
from ..utility import *
from .operating_mode import OperatingMode


@dataclass
class CyclicSynchronousVelocityAddresses:
    velocity_actual_value: int = 0x606C
    target_velocity: int = 0x60FF
    software_position_limit: int = 0x607D
    velocity_offset: int = 0x60B1
    interpolation_time_period: int = 0x60C2

class CyclicSynchronousVelocity(OperatingMode):
    def __init__(self, node: RemoteNode):
        self._node = node
        self.profile_code = 9
        self.addresses = CyclicSynchronousVelocityAddresses()

    def set_command(self, value):
        self.set_velocity(int(value))

    def set_velocity(self, velocity):
        """Set the desired velocity. This object must be written cyclically with the speed set value.

        Args:
            velocity (int): target velocity, given in user defined speed units
        """
        self._node.sdo[self.addresses.target_velocity].raw = int32(velocity)

    def get_velocity(self):
        """Current velocity

        Returns:
            int: current actual speed in user-defined units
        """
        return self._node.sdo[self.addresses.velocity_actual_value].raw

    def set_velocity_offset(self, offset):
        """Set the offset for the speed value.

        Args:
            offset (int): offset, given in user-defined units
        """

        self._node.sdo[self.addresses.velocity_offset].raw = int32(offset)

    def set_interpolation_time(self, base, exponent):
        """Set the interpolation time period.

        Interpolation time = base * 10^exponent

        Args:
            base (int): interpolation time
            exponent (int): power of ten of the interpolation time
        """
        self._node.sdo.download(self.addresses.interpolation_time_period, 1, uint8(int(base)))
        self._node.sdo.download(self.addresses.interpolation_time_period, 2, int8(int(exponent)))
