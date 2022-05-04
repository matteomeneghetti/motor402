from typing import Iterable, Tuple, Union
import canopen
import time
from threading import Thread

from configs import TPDOConfig, RPDOConfig
from utility import *
from state import SW_MASK, TRANSITIONTABLE, to_operation_enabled_map

index_map = {
    "no_mode": {
        "value": 0,
        "index_map": {}
    },
    "pp": {
        "value": 1,
        "index_map": {
            "position_demand_value": 0x6062,
            "position_actual_internal_value": 0x6063,
            "position_actual_value": 0x6064,
            "following_error_window": 0x6065,
            "position_window": 0x6067,
            "position_window_time": 0x6068,
            "velocity_actual_value": 0x606C,
            "target_position": 0x607A,
            "software_position_limit": 0x607D,
            "profile_velocity": 0x6081,
            "end_velocity": 0x6082,
            "profile_acceleration": 0x6083,
            "profile_deceleration": 0x6084,
            "quick_stop_deceleration": 0x6085,
            "positioning_option_code": 0x60F2,
        },
    },
    "common": {"controlword": 0x6040, "statusword": 0x6041, "operating_mode": 0x6060, "switch": 0x2005},
}

rename_map = {
    "controlword": "Controlword 1",
    "statusword": "Statusword 1",
    "operating_mode": "Modes of Operation 1",
    "target_position": "Target Position 1"
}

motion_profiles_cfg = {
    "index": "operating_mode",
    "profiles": {
        "no_mode": 0,
        "pp": 1
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
            for data in self.data_generator():
                if not self.running:
                    break
                for (index, subindex), d in zip(self.indexes, data):
                    var = self.pdo[index]
                    if not isinstance(var, canopen.pdo.Variable):
                        var = var[subindex]
                    var.raw = d
                self.pdo.transmit()
                time.sleep(1 / self.frequency)

        def start(self):
            self.thread = Thread(target=self.run)
            self.thread.start()

        def stop(self):
            self.running = False
            self.thread.join()

    def __init__(
        self,
        node: canopen.RemoteNode,
        rename_map: dict = rename_map,
        motion_profiles: dict = motion_profiles_cfg
    ):

        self._node = node
        self.rpdo_tasks = {}
        self.tpdo = {}
        self.tpdo_values = {}

        self.rename_map = rename_map
        self.operating_mode_map = motion_profiles
        self._operating_mode = 0

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

            # self._node.tpdo[pdo_config.index].event_timer = pdo_config.event_timer
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


    def get(self, variable_index, variable_subindex=0, property:str='raw'):
        index, subindex = self._look_up(variable_index, variable_subindex)

        # Look up if the requested variable is currently being updated through PDOs
        if (index, subindex) in self.tpdo_values:
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
        for state, mask_val_pair in SW_MASK.items():
            bitmask, bits = mask_val_pair
            if self.get('statusword') & bitmask == bits:
                return state
        return 'UNKNOWN'

    @state.setter
    def state(self, new_state:str):

        if self.state == new_state:
            return

        if new_state not in SW_MASK:
            raise ValueError

        transition = (self.state, new_state)
        if transition not in TRANSITIONTABLE:
            raise ValueError

        self.set('controlword', uint16(TRANSITIONTABLE[transition]))

        self.state

    @property
    def is_faulted(self):
        return self.state == 'FAULT'

    def recover_from_fault(self):
        self.state = 'SWITCH ON DISABLED'

    def to_operational(self):
        transitions = to_operation_enabled_map[self.state]
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
                self.set(op_mode_index, value, subindex=op_mode_subindex)
        else:
            raise ValueError

    def pdo_callback(self, msg):
        for var in msg:
            self.tpdo_values[(var.index, var.subindex)] = var


if __name__ == "__main__":
    network = canopen.Network()
    node = canopen.RemoteNode(0x75, "./examples/backripper/TMCM-6212.eds")
    network.add_node(node)
    network.connect(bustype="pcan", channel="PCAN_USBBUS1", bitrate=1000000)
    time.sleep(0.1)

    node.nmt.state = "PRE-OPERATIONAL"
    node.tpdo.read()
    node.rpdo.read()

    tpdos = [
        TPDOConfig(
            1, ("operating_mode",), rtr_allowed=False, enabled=False
        ),
        TPDOConfig(3, ("target_position",), rtr_allowed=False, enabled=False),
    ]

    def generator():
        for i in range(1000000):
            yield (i,)

    rpdos = [
        RPDOConfig(
            1, ("target_position",), data=generator, frequency=100, rtr_allowed=False
        )
    ]

    motor = Motor(node)
    node.nmt.state = "OPERATIONAL"
    motor.operating_mode = 'pp'
    motor.set(0x2005, uint32(3))
    print(motor.state)
    motor.to_operational()
    motor.set(0x607A, int32(int(50/0.0127*256)))
    motor.set('controlword', uint16(31))
    print(motor.state)
    # motor.set_tpdos(tpdos)
    # motor.set_rpdos(rpdos)
    # network.sync.start(0.1)
    # motor.start_rpdo(1)

    while True:
        time.sleep(1)
