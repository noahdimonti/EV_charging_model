from collections import defaultdict
from pprint import pprint
import pandas as pd
import numpy as np
import os
from src.config import params


def to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: to_dict(v) for k, v in d.items()}
    elif isinstance(d, dict):
        d = {k: to_dict(v) for k, v in d.items()}
    return d


def build_payoff_tables(versions: list):
    payoff_table = defaultdict(lambda: defaultdict(list))

    for version in versions:
        filename = f'raw_values_compiled_metrics_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv'
        filepath = os.path.join(params.compiled_metrics_folder_path, filename)

        df = pd.read_csv(filepath, index_col=0)

        for model in df.columns:
            econ = df.loc['economic_objective', model]
            tech = df.loc['technical_objective', model]
            soc = df.loc['social_objective', model]

            payoff_table[model]['economic'].append(econ)
            payoff_table[model]['technical'].append(tech)
            payoff_table[model]['social'].append(soc)

    return payoff_table


def get_min_max_obj_values(payoff_table: dict):
    obj_min_max = defaultdict(lambda: defaultdict(list))
    objectives = ['economic', 'technical', 'social']

    for model, values in payoff_table.items():
        for obj in objectives:
            min_val = np.min(values[obj])
            max_val = np.max(values[obj])

            obj_min_max[model][f'{obj}_min'] = min_val
            obj_min_max[model][f'{obj}_max'] = max_val

    filepath = os.path.join(params.compiled_metrics_folder_path, 'payoff_table.py')

    # Convert defaultdict into dict
    payoff = to_dict(obj_min_max)

    # write to a Python file
    with open(filepath, 'w') as f:
        f.write('payoff_table = ')
        pprint(payoff, stream=f, indent=4, width=120, sort_dicts=False)

    return payoff_table


if __name__ == '__main__':
    payoff = build_payoff_tables(['min_econ', 'min_tech', 'min_soc'])
    get_min_max_obj_values(payoff)






