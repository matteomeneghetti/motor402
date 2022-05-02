from typing import Iterable

class PDOConfig:

    def __init__(self, index, variables: Iterable = tuple(), **kwargs):
        self.index = index
        self.variables = variables

        self.event_timer = kwargs.get('event_timer', 100)
        self.rtr_allowed = kwargs.get('rtr_allowed', True)
        self.trans_type = kwargs.get('trans_type', 10)
        self.enabled = kwargs.get('enabled', True)

tpdo_templates = {
    'pp': [
        PDOConfig(1, ('statusword')),
        PDOConfig(2, ('statusword', 'position_actual_value')),
        PDOConfig(3, ('statusword', 'position_actual_internal_value'), enabled=False),
        PDOConfig(4, (), enabled=False)
    ]
}
