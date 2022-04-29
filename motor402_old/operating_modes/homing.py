from dataclasses import dataclass
from canopen import RemoteNode
from ..utility import *

@dataclass
class HomingAddresses:
    velocity_actual_value: int = 0x606C
    home_offset: int = 0x607C
    homing_method: int = 0x6098
    homing_speeds: int = 0x6099
    homing_acceleration: int = 0x609A

class Homing:

    def __init__(self, node: RemoteNode):
        self._node = node
        self.profile_code = 6
        self.addresses = HomingAddresses()

    def get_velocity(self):
        return self._node.sdo[self.addresses.velocity_actual_value].raw

    def set_homing_speeds(self, values):
        self._node.sdo.download(self.addresses.homing_speeds, 1, uint32(int(values[0])))
        self._node.sdo.download(self.addresses.homing_speeds, 2, uint32(int(values[1])))

    def get_home_offset(self):
        return self._node.sdo[self.addresses.home_offset].raw

    def set_homing_method(self, value):
        self._node.sdo[self.addresses.homing_method].raw = int8(value)
