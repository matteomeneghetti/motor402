from typing import Iterable
import canopen
import time
from threading import Thread

from .configs import TPDOConfig, RPDOConfig
from .utility import *
from .state import SW_MASK, TRANSITIONTABLE, to_operation_enabled_map, to_switch_on_disabled

default_motion_profiles_cfg = {
    "index": 0x6060,
    "profiles": {
        "no_mode": 0,
        "pp": 1,
        "pv": 2,
        "hm": 6,
        "csp": 8,
        "csv": 9
    }
}

class Motor:
    class _Task:
        def __init__(self, pdo, indexes, data_generator, frequency):
            self.pdo = pdo
            self.indexes = indexes
            self.data_generator = data_generator
            self.frequency = frequency
            self.running = False
            self.thread = None

        def run(self):
            self.running = True
            for data in self.data_generator:
                if not self.running:
                    break
                for (index, subindex), d in zip(self.indexes, data):
                    var = self.pdo[index]
                    if not isinstance(var, canopen.pdo.Variable):
                        var = var[subindex]
                    var.raw = d
                self.pdo.transmit()
                time.sleep(1 / self.frequency)
            self.running = False

        def start(self):
            self.thread = Thread(target=self.run)
            self.thread.start()

        def stop(self):
            if not self.running:
                return
            self.running = False
            self.thread.join()

    def __init__(
        self,
        node: canopen.RemoteNode,
        rename_map: dict,
        motion_profiles: dict=default_motion_profiles_cfg,
        *,
        controlword_index=0x6040,
        statusword_index=0x6041
    ):

        self._node = node
        self.rpdo_tasks = {}
        self.tpdo = {}
        self.tpdo_values = {}

        self.rename_map = rename_map
        self.operating_mode_map = motion_profiles
        self._operating_mode = 0
        self._cw_index = controlword_index
        self._sw_index = statusword_index

    def move_to_target(self, value, *, target_index='target_position', profile='pp', relative=False):
        self.to_switch_on_disabled()
        self.operating_mode = profile
        self.to_operational()

        self.set(target_index, int32(value))
        move_command = 31
        if relative:
            move_command |= 64
        self.set(self._cw_index, uint16(move_command))
        self.set(self._cw_index, uint16(15))

    def follow_trajectory(self, rpdo_cfg, *, profile='csp'):
        if not isinstance(rpdo_cfg, RPDOConfig):
            raise TypeError("rpdo_cfg must be of type" + RPDOConfig.__class__)
        self.to_switch_on_disabled()

        self.set_rpdos((rpdo_cfg,))

        self.operating_mode = profile
        self.to_operational()

        self.start_rpdo(rpdo_cfg.index)


    def home(self, homing_method: int, homing_speed_fast: float, homing_speed_slow: float, homing_acc: float):
        self.to_switch_on_disabled()
        self.operating_mode = 'hm'
        self.to_operational()
        self.set('homing_method', int8(homing_method))
        self.set('homing_speeds', uint32(homing_speed_fast), subindex=1) #256*8/0.0127
        self.set('homing_speeds', uint32(homing_speed_slow), subindex=2)
        self.set('homing_acceleration', uint32(homing_acc))
        self.set(self._cw_index, uint16(31))

    def shutdown(self):
        self.to_switch_on_disabled()

        for tpdo_index in self.tpdo:
            self.clear_tpdo(tpdo_index)

        for index, task in self.rpdo_tasks.items():
            task.stop()
            self.clear_rpdo(index)

        self.rpdo_tasks.clear()

    def set_tpdos(self, configs: Iterable[TPDOConfig]):

        for pdo_config in configs:
            if not isinstance(pdo_config, TPDOConfig):
                raise TypeError
            self._node.tpdo[pdo_config.index].clear()

            for index in pdo_config.variables:

                subindex = 0
                if isinstance(index, Iterable) and not isinstance(index, str):
                    index, subindex = index
                index, subindex = self._look_up(index, subindex)

                var =  self._node.tpdo[pdo_config.index].add_variable(index, subindex)
                if pdo_config.enabled:
                    self.tpdo_values[(index, subindex)] = var

            self._node.tpdo[pdo_config.index].event_timer = pdo_config.event_timer
            self._node.tpdo[pdo_config.index].trans_type = pdo_config.trans_type
            self._node.tpdo[pdo_config.index].rtr_allowed = pdo_config.rtr_allowed
            self._node.tpdo[pdo_config.index].enabled = pdo_config.enabled
            self._node.tpdo[pdo_config.index].save()

            self._node.tpdo[pdo_config.index].add_callback(self.pdo_callback)
            self.tpdo[pdo_config.index] = self._node.tpdo[pdo_config.index]

    def set_rpdos(self, configs: Iterable[RPDOConfig]):

        for pdo_config in configs:
            if not isinstance(pdo_config, RPDOConfig):
                raise TypeError
            self._node.rpdo[pdo_config.index].clear()

            variables_list = []

            for index in pdo_config.variables:

                subindex = 0
                if isinstance(index, Iterable) and not isinstance(index, str):
                    index, subindex = index
                index, subindex = self._look_up(index, subindex)

                self._node.rpdo[pdo_config.index].add_variable(index, subindex)
                variables_list.append((index, subindex))

            self._node.rpdo[pdo_config.index].rtr_allowed = pdo_config.rtr_allowed
            self._node.rpdo[pdo_config.index].trans_type = pdo_config.trans_type
            self._node.rpdo[pdo_config.index].enabled = pdo_config.enabled
            self._node.rpdo[pdo_config.index].save()

            self.rpdo_tasks[pdo_config.index] = Motor._Task(
                self._node.rpdo[pdo_config.index],
                variables_list,
                pdo_config.data,
                pdo_config.frequency,
            )

    def _look_up(self, index, subindex=0):
        index = self.rename_map.get(index, False) or index
        subindex = self.rename_map.get(subindex, False) or subindex
        var = self._node.object_dictionary.get_variable(index, subindex)
        return (var.index, var.subindex)

    def clear_tpdo(self, index: int):
        self.tpdo[index].clear()
        self.tpdo[index].enabled = False
        self.tpdo[index].save()

    def clear_rpdo(self, index: int):
        self.rpdo_tasks[index].stop()
        self.rpdo_tasks[index].pdo.clear()
        self.rpdo_tasks[index].enabled = False
        self.rpdo_tasks[index].pdo.save()

    def start_rpdo(self, index):
        self.rpdo_tasks[index].start()


    def get(self, variable_index, variable_subindex=0, property:str='raw', force_sdo=False):
        index, subindex = self._look_up(variable_index, variable_subindex)

        # Look up if the requested variable is currently being updated through PDOs
        if not force_sdo and (index, subindex) in self.tpdo_values:
            return getattr(self.tpdo_values[(index, subindex)], property)

        var = self._node.sdo[index]
        if not isinstance(var, canopen.sdo.Variable):
            var = var[subindex]
        return getattr(var, property)

    def set(self, variable_index, value, property:str='raw', *, subindex=None):
        index, subindex = self._look_up(variable_index, subindex)
        var = self._node.sdo[index]
        if not isinstance(var, canopen.sdo.Variable):
            var = var[subindex]
        return setattr(var, property, value)

    @property
    def state(self):
        sw = self.get(self._sw_index, force_sdo=True)
        for state, mask_val_pair in SW_MASK.items():
            bitmask, bits = mask_val_pair
            if sw & bitmask == bits:
                return state
        print(f"SW: {bin(sw)}")
        return 'UNKNOWN'

    @state.setter
    def state(self, new_state:str):

        if self.state == new_state:
            return

        if new_state not in SW_MASK:
            raise ValueError

        transition = (self.state, new_state)
        if transition not in TRANSITIONTABLE:
            raise ValueError(f"Can't go from {transition[0]} to {transition[1]}")

        self.set(self._cw_index, uint16(TRANSITIONTABLE[transition]))


    @property
    def is_faulted(self):
        return self.state == 'FAULT'

    def recover_from_fault(self):
        self.state = 'SWITCH ON DISABLED'

    def to_operational(self):
        transitions = to_operation_enabled_map[self.state]
        for state in transitions:
            self.state = state

    def to_switch_on_disabled(self):
        transitions = to_switch_on_disabled[self.state]
        for state in transitions:
            self.state = state

    @property
    def operating_mode(self):
        return self.get(self._look_up(self.operating_mode_map['index']))

    @operating_mode.setter
    def operating_mode(self, mode):
        if mode in self.operating_mode_map['profiles']:
            value = self._operating_mode = self.operating_mode_map['profiles'][mode]
            op_mode_index, op_mode_subindex = self._look_up(self.operating_mode_map['index'])
            if value != self.get(op_mode_index, op_mode_subindex):
                self.to_switch_on_disabled()
                self.set(op_mode_index, value, subindex=op_mode_subindex)
        else:
            raise ValueError

    def pdo_callback(self, msg):
        for var in msg:
            self.tpdo_values[(var.index, var.subindex)] = var
