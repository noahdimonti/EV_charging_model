import json
from src.pipelines.analyse_results import load_model
from pprint import pprint


config = 'config_2'
strategy = 'opportunistic'
version_1 = 'balanced'
version_2 = '2703'


model_results_1 = load_model(config, strategy, version_1)

model_results_2 = load_model(config, strategy, version_2)

vars_1 = model_results_1.__dict__['variables']
vars_2 = model_results_2.__dict__['variables']

for var_name in vars_1:
    v1 = vars_1[var_name]
    v2 = vars_2.get(var_name)

    if v1 == v2:
        continue

    print(f'\n===== DIFF in {var_name} =====')

    # if both are dict-like, compare key by key
    if isinstance(v1, dict) and isinstance(v2, dict):
        all_keys = set(v1.keys()) | set(v2.keys())

        for key in sorted(all_keys):
            val1 = v1.get(key, '<MISSING>')
            val2 = v2.get(key, '<MISSING>')

            if val1 != val2:
                print(f'{key}: {val1}  !=  {val2}')

    else:
        print('v1:')
        pprint(v1)
        print('v2:')
        pprint(v2)