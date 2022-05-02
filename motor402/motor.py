from typing import Iterable
import canopen
import time

from configs import PDOConfig

index_map = {
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
    "common": {"controlword": 0x6040, "statusword": 0x6041, "operating_mode": 0x6060},
}


def _init_indexmap(indexmap) -> dict:
    cache = dict()
    for name, index in indexmap.items():
        if isinstance(index, Iterable):
            var = Motor._Variable(name, index[0], index[1] if len(index) > 1 else 0)
            cache[name] = var
            cache[
                (index[0], index[1] if len(index) > 1 else 0)
            ] = var  #!non c'era alternativa
        elif isinstance(index, int):
            var = Motor._Variable(name, index)
            cache[name] = var
            cache[(index, 0)] = var
        else:
            raise TypeError("Index should be a tuple(int[,int]) or an int")
    return cache


class Motor:
    class _Variable:
        def __init__(self, name, index, subindex=0):
            self.name = name
            self.index = index
            self.subindex = subindex
            self.update_through_pdo = False
            self.value = None  # type pdo.base.Variable

        # def __eq__(self, value):
        #     if isinstance(value, Motor._Variable):
        #         return self.name == value.name
        #     elif isinstance(value, str):
        #         return self.name == value
        #     elif isinstance(value, int):
        #         return self.index == value
        #     elif isinstance(value, Iterable) and len(value) >= 2:
        #         return (self.index, self.subindex) == value[:2]
        #     else:
        #         raise TypeError("cannot compare " + type(self) + " with " + type(value))

    # class _VariableKey:

    #     def __init__(self, name, index, subindex=0):
    #         self.name = name
    #         self.index = index
    #         self.subindex = subindex

    #     def __eq__(self, value):
    #         if isinstance(value, Motor._Variable):
    #             return self.name == value.name
    #         elif isinstance(value, str):
    #             return self.name == value
    #         elif isinstance(value, int):
    #             return self.index == value
    #         elif isinstance(value, Iterable) and len(value) >= 2:
    #             return (self.index, self.subindex) == value[:2]
    #         return False

    #     def __hash__(self) -> int:
    #         return hash((self.name, self.index, self.subindex))

    # 1. Usare 2 dict
    # 2. Override __getitem__

    class _OperatingMode:
        def __init__(self, value: int, index_map: dict):
            self.value = value
            self.variables = _init_indexmap(index_map)
            # for key, item in index_map.items():
            #     if isinstance(item, Iterable) and len(item) > 1:
            #         key = Motor._VariableKey(key, item[0], item[1])
            #         var = Motor._Variable()
            #     else:
            #         key = Motor._VariableKey(key, item)
            #         var = Motor._Variable()
            #     self.variables[key] = var

    def __init__(
        self,
        node: canopen.RemoteNode,
        tpdos: Iterable = (),
        index_map: dict = index_map,
    ):

        self._node = node
        self._operating_mode = "pp"

        self.operating_modes = dict()
        for key, item in index_map.items():
            if key == "common":
                continue
            self.operating_modes[key] = Motor._OperatingMode(
                item["value"], item["index_map"]
            )

        self.common_variables = _init_indexmap(index_map["common"])
        self._init_tpdos(tpdos)

    def _init_tpdos(self, configs: Iterable[PDOConfig]):

        for pdo_config in configs:
            if type(pdo_config) != PDOConfig:
                raise TypeError
            self._node.tpdo[pdo_config.index].clear()

            for variable_key in pdo_config.variables:

                if isinstance(variable_key, int):
                    variable_key = (variable_key, 0)

                variable = self.common_variables.get(variable_key, None)
                if variable is None:
                    variable = self.operating_modes[self._operating_mode].variables[
                        variable_key
                    ]

                # if variable_key in self.common_variables:
                #     variable = self.common_variables[variable_key]

                # elif (
                #     variable_key in self.operating_modes[self._operating_mode].variables
                # ):
                #     variable = self.operating_modes[self._operating_mode].variables[
                #         variable_key
                #     ]
                # else:
                #     raise IndexError

                self._node.tpdo[pdo_config.index].add_variable(
                    variable.index, variable.subindex
                )
                variable.update_through_pdo = True

            # self._node.tpdo[pdo_config.index].event_timer = pdo_config.event_timer
            self._node.tpdo[pdo_config.index].trans_type = pdo_config.trans_type
            self._node.tpdo[pdo_config.index].rtr_allowed = pdo_config.rtr_allowed
            self._node.tpdo[pdo_config.index].enabled = pdo_config.enabled
            self._node.tpdo[pdo_config.index].save()

            self._node.tpdo[pdo_config.index].add_callback(self.pdo_callback)

    def set_operating_mode(self, mode: str):

        if mode in self.operating_modes:
            self._operating_mode = mode
        else:
            raise ValueError

    def pdo_callback(self, msg):
        for var in msg:
            if (var.index, var.subindex) in self.common_variables:
                self.common_variables[(var.index, var.subindex)].value = var
                print(f"Common -> {self.common_variables[(var.index, var.subindex)].name}: {var.raw}")
            elif (var.index, var.subindex) in self.operating_modes[
                self._operating_mode
            ].variables:
                self.operating_modes[self._operating_mode].variables[
                    (var.index, var.subindex)
                ].value = var
                print(f"{self._operating_mode}: {var.raw}")
            else:
                raise ValueError


if __name__ == "__main__":
    network = canopen.Network()
    node = canopen.RemoteNode(0x75, "./examples/backripper/TMCM-6212.eds")
    network.add_node(node)
    network.connect(bustype="pcan", channel="PCAN_USBBUS1", bitrate=1000000)
    time.sleep(0.1)

    node.nmt.state = "PRE-OPERATIONAL"
    node.tpdo.read()
    config = PDOConfig(
        1, ("statusword", "operating_mode", "statusword"), rtr_allowed=False
    )
    config3 = PDOConfig(3, tuple(), enabled=False)
    motor = Motor(node, [config, config3])
    node.nmt.state = "OPERATIONAL"
    network.sync.start(0.1)
    while True:
        time.sleep(0.2)
