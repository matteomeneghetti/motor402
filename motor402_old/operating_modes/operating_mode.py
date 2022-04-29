from abc import ABC, abstractmethod
from canopen.profiles.p402 import OperationMode

class OperatingMode(ABC):

    profile_code = OperationMode.NO_MODE

    @abstractmethod
    def set_command(self, value):
        """Execute the default profile command

        Args:
            value ([type]): [description]
        """
        pass
