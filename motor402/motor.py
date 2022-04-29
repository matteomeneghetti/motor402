from typing import Iterable
import canopen
import time

class PDOConfig:

    def __init__(self, index, variables: Iterable = tuple(), **kwargs):
        self.index = index
        self.variables = variables
        # for key, item in kwargs.items():
        #     self.__dict__[key] = item
        self.event_timer = kwargs.get('event_timer', 100)
        self.rtr_allowed = kwargs.get('rtr_allowed', True)
        self.trans_type = kwargs.get('trans_type', 10)
        self.enabled = kwargs.get('enabled', True)

default_addresses = {
    'controlword': 0x6040,
    'statusword': 0x6041,
    'operating_mode': 0x6060
}

index_map = {
    'pp': {
        'value': 1,
        'index_map': {
            'position_demand_value': 0x6062,
            'position_actual_internal_value': 0x6063,
            'position_actual_value': 0x6064,
            'following_error_window': 0x6065,
            'position_window': 0x6067,
            'position_window_time': 0x6068,
            'velocity_actual_value': 0x606C,
            'target_position': 0x607A,
            'software_position_limit': 0x607D,
            'profile_velocity': 0x6081,
            'end_velocity': 0x6082,
            'profile_acceleration': 0x6083,
            'profile_deceleration': 0x6084,
            'quick_stop_deceleration': 0x6085,
            'positioning_option_code': 0x60F2,
        }
    },
    'common': {
        'controlword': 0x6040,
        'statusword': 0x6041,
        'operating_mode': 0x6060
    }
}




class Motor:

    class _Variable:

        def __init__(self, name: str, index: int, subindex: int = 0):
            self.name = name
            self.index = index
            self.subindex = subindex
            self.update_through_pdo = False
            self.value = None # type Variable

        def __eq__(self, value):
            if isinstance(value, Motor._Variable):
                return self.name == value.name
            elif isinstance(value, str):
                return self.name == value
            elif isinstance(value, int):
                return self.index == value
            elif isinstance(value, Iterable) and len(value) >= 2:
                return (self.index, self.subindex) == value[:2]
            else:
                raise TypeError("cannot compare " + type(self) + " with " + type(value))

    class _OperatingMode:

        def __init__(self, value: int, index_map: dict):
            self.value = 0
            self.variables = []
            for key, item in index_map.items():
                if isinstance(item, Iterable) and len(item) > 1:
                    var = Motor._Variable(key, item[0], item[1])
                else:
                    var = Motor._Variable(key, item)
                self.variables.append(var)


    def __init__(self, node: canopen.RemoteNode, tpdos: Iterable = (), index_map: dict = index_map):

        self._node = node
        self._operating_mode = None

        self.operating_modes = dict()
        for key, item in index_map.items():
            if key == 'common':
                continue
            self.operating_modes[key] = Motor._OperatingMode(item['value'], item['index_map'])

        self.common_variables = []
        for key, item in index_map['common'].items():
            if isinstance(item, Iterable) and len(item) > 1:
                var = Motor._Variable(key, item[0], item[1])
            else:
                var = Motor._Variable(key, item)
            self.common_variables.append(var)

        self._init_tpdos(tpdos)

    def _init_tpdos(self, configs: Iterable[PDOConfig]):

        for pdo_config in configs:
            if type(pdo_config) != PDOConfig:
                raise TypeError
            self._node.tpdo[pdo_config.index].clear()

            for variable_name in pdo_config.variables:
                if variable_name in self.common_variables:
                    variable = self.common_variables[self.common_variables.index(variable_name)]
                elif variable_name in self.operating_modes[self._operating_mode].variables:
                    var_list = self.operating_modes[self._operating_mode].variables
                    variable = var_list[var_list.index(variable_name)]
                else:
                    raise IndexError

                self._node.tpdo[pdo_config.index].add_variable(variable.index, variable.subindex)
                variable.update_through_pdo = True

            #self._node.tpdo[pdo_config.index].event_timer = pdo_config.event_timer
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
        # op_mode_var_list = self.operating_modes[self._operating_mode].variables
        # for var in msg:
        #     variable = None
        #     print(var)
        #     if var.index in self.common_variables:
        #         print(self.common_variables.index(var.index))
        #         variable = self.common_variables[self.common_variables.index(var.index)]
        #         variable.value = var.copy()
        #     elif var.index in op_mode_var_list:
        #         print(self.common_variables.index(var.index))
        #         variable = op_mode_var_list[op_mode_var_list.index(var.index)]
        #         variable.value = var.copy()
        #     else:
        #         print("ciao")

        # op_mode_var_list = self.operating_modes[self._operating_mode].variables
        print(self._operating_mode)
        for var in msg:
            if var.index in self.common_variables:
                variable = self.common_variables[self.common_variables.index(var.index)]
                variable.value = var
                print(variable)

if __name__ == "__main__":
    network = canopen.Network()
    node = canopen.RemoteNode(0x75, '../examples/backripper/TMCM-6212.eds')
    network.add_node(node)
    network.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=1000000)
    time.sleep(0.1)

    node.nmt.state = 'PRE-OPERATIONAL'
    node.tpdo.read()
    config = PDOConfig(1, ('statusword','operating_mode', 'statusword'), rtr_allowed=False)
    config3 = PDOConfig(3, tuple(), enabled=False)
    motor = Motor(node, [config, config3])
    node.nmt.state = 'OPERATIONAL'
    network.sync.start(0.1)
    while True:
        time.sleep(0.2)
