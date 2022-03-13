from dataclasses import dataclass
from canopen import RemoteNode
from abc import ABC, abstractmethod
from ..utility import *
from .operating_mode import OperatingMode

@dataclass
class CyclicSynchronousPositionAddresses:
    position_demand_value: int = 0x6062
    position_actual_internal_value: int = 0x6063
    position_actual_value: int = 0x6064
    velocity_actual_value: int = 0x606C
    target_position: int = 0x607A
    software_position_limit: int = 0x607D
    position_offset: int = 0x60B0
    interpolation_time_period: int = 0x60C2