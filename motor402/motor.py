from canopen import RemoteNode
from canopen.profiles.p402 import State402, OperationMode
from dataclasses import dataclass
from .operating_modes import OperatingMode
import time
from .utility import *

@dataclass
class Addresses:
    controlword: int = 0x6040
    statusword: int = 0x6041
    operation_mode: int = 0x6060

class Motor:

    def __init__(self, board: RemoteNode):
        self._node = board
        self.addresses = Addresses()
        self.operatingMode = None

    def attach(self, operatingMode: OperatingMode):
        """Attach an Operating Mode to the motor

        Args:
            operatingMode (OperatingMode): operating mode
        """
        self.operatingMode = operatingMode
        #self.operation_mode = self.operatingMode.profile_code

    @property
    def statusword(self):
        """Return the raw statusword
        """
        return self._node.sdo[self.addresses.statusword].raw

    @property
    def controlword(self):
        raise NotImplementedError("Can't read Controlword")

    @controlword.setter
    def controlword(self, value):
        """_summary_

        Args:
            value (_type_): _description_
        """
        self._node.sdo[self.addresses.controlword].raw = uint16(value)

    @property
    def state(self)-> str:
        """
        Returns:
            str: current 402 state as a string
        """
        for state, mask_val_pair in State402.SW_MASK.items():
            bitmask, bits = mask_val_pair
            if self.statusword & bitmask == bits:
                return state
        return 'UNKNOWN'

    @state.setter
    def state(self, desired_state):
        while self.state != desired_state:
            next_state = self._next_state(desired_state)
            if self._change_state(next_state):
                continue
            if time.monotonic() > 0.5:
                raise RuntimeError('Timeout when trying to change state')
            self.check_statusword()

    def _next_state(self, target_state):
        if target_state in ('NOT READY TO SWITCH ON',
                            'FAULT REACTION ACTIVE',
                            'FAULT'):
            raise ValueError(
                'Target state {} cannot be entered programmatically'.format(target_state))
        from_state = self.state
        if (from_state, target_state) in State402.TRANSITIONTABLE:
            return target_state
        else:
            return State402.next_state_for_enabling(from_state)

    def _change_state(self, target_state):
        try:
            self.controlword = State402.TRANSITIONTABLE[(self.state, target_state)]
        except KeyError:
            raise ValueError(
                'Illegal state transition from {f} to {t}'.format(f=self.state, t=target_state))
        timeout = time.monotonic() + 0.5
        while self.state != target_state:
            if time.monotonic() > timeout:
                return False
        return True

    @property
    def is_power_enabled(self):
        return self.statusword & 0x02

    @property
    def is_torque_enabled(self):
        return self.statusword & 0x04

    @property
    def is_faulted(self):
        bitmask, bits = State402.SW_MASK['FAULT']
        return self.statusword & bitmask == bits

    @property
    def operation_mode(self):
        return self._node.sdo[self.addresses.operation_mode].raw #OperationMode.CODE2NAME[self._node.sdo[self.addresses.operation_mode].raw]

    @operation_mode.setter
    def operation_mode(self, desired_mode):
        self._recover_from_fault()
        if self.is_power_enabled:
            raise ValueError("Can't change operation mode: power is enabled")
        if type(desired_mode) == int:
            self._node.sdo[self.addresses.operation_mode].raw = uint8(desired_mode)
        else:
            self._node.sdo[self.addresses.operation_mode].raw = uint8(OperationMode.NAME2CODE[desired_mode])

    def _recover_from_fault(self):
        #if self.is_faulted:
        self.state = 'SWITCH ON DISABLED'
        while self.is_faulted:
            time.sleep(0.01)

    def _move(self, value):
        self.state = 'OPERATION ENABLED'
        self.operatingMode.set_command(value)
        self.controlword = 31 # Target is active

    def move(self, value):
        self._move(value)
