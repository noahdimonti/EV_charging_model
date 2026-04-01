import os

obj_weights_type = os.getenv('OBJ_WEIGHTS_TYPE', 'balanced')
debugging_version = os.getenv('DEBUGGING_VERSION', '')
version = f'{obj_weights_type}{debugging_version}'

configurations = [
    'config_1',
    'config_2',
    'config_3',
]

charging_strategies = [
    'uncoordinated',
    'opportunistic',
    'flexible',
]