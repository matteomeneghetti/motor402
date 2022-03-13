from dataclasses import dataclass
from canopen import RemoteNode
from abc import ABC, abstractmethod
from enum import Enum
from ..utility import *

class OperatingMode(ABC):

    profile_code = 0

    @abstractmethod
    def set_command(self, value):
        """Execute the default profile command

        Args:
            value ([type]): [description]
        """
        pass

class OperatingModeCode(Enum):

    NO_MODE = 0
    PROFILE_POSITION = 1
    VELOCITY = 2
    PROFILE_VELOCITY = 3
    PROFILE_TORQUE = 4
    RESERVED = 5
    HOMING = 6
    INTERPOLATED_POSITION = 7
    CYCLIC_SYNCHRONOUS_POSITION = 8
    CYCLIC_SYNCHRONOUS_VELOCITY = 9
    CYCLIC_SYNCHRONOUS_TORQUE = 10