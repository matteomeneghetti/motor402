from typing import Iterable

class TPDOConfig:

    def __init__(self, index, variables: Iterable = tuple(), **kwargs):
        self.index = index
        self.variables = variables
        self.trans_type = kwargs.get('trans_type', 255)
        self.event_timer = kwargs.get('event_timer', 0)
        if self.trans_type != 255 and self.event_timer != 0:
            raise ValueError
        self.rtr_allowed = kwargs.get('rtr_allowed', True)
        self.enabled = kwargs.get('enabled', True)

class RPDOConfig:

    def __init__(self, index, variables: Iterable = tuple(), **kwargs):
        self.index = index
        self.variables = variables

        self.data = kwargs.get('data', ())
        self.frequency = kwargs.get('frequency', 0)
        self.rtr_allowed = kwargs.get('rtr_allowed', True)
        self.trans_type = kwargs.get('trans_type', None)
        self.enabled = kwargs.get('enabled', True)


tpdo_templates = {
    'pp': [
        TPDOConfig(1, ('statusword')),
        TPDOConfig(2, ('position_demand_value', 'position_actual_value')),
        TPDOConfig(3, (), enabled=False),
        TPDOConfig(4, (), enabled=False)
    ]
}
