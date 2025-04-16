import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import pyomo.environ as pyo
import itertools
from src.models.optimisation_models.build_model import BuildModel
from src.models.optimisation_models.solve_model import solve_optimisation_model
from src.models.optimisation_models.objectives import EconomicObjective, TechnicalObjective, SocialObjective
from src.models.mapping import config_map, strategy_map
from scripts.execute_models import execute_model
from scripts.analyse_results import analyse_results
from src.config import independent_variables, params
from pprint import pprint

# Generate weights that sum to 1
step = 1
w_vals = np.arange(0, 1 + step, step)

weight_dicts = []
for w1, w2 in itertools.product(w_vals, repeat=2):
    w3 = 1 - w1 - w2
    if 0 <= w3 <= 1:
        weight_dicts.append({
            'economic': w1,
            'technical': w2,
            'social': round(w3, 10)
        })

# Run optimisation for each weight
config = 'config_1'
strategy = 'opportunistic'
version = 'sensitivity_analysis'
num_ev = params.num_of_evs
verbose = False
time_limit = 10
mip_gap = 0.9

df = pd.DataFrame()

for weights in weight_dicts:
    print(f'\nw: {weights}')

    execute_model(
        config,
        strategy,
        version,
        weights
    )

    raw, formatted = analyse_results([config], [strategy], version, num_ev)

    df = pd.concat([raw, df], axis=1)

print(df)


df = df.T  # Transpose so each row is one config

# Define metrics: lower is better vs higher is better
lower_better = [
    'investment_cost',
    'avg_p_peak',
    'avg_papr',
    'avg_daily_peak_increase',
    'total_cost_per_user'
]
higher_better = [
    'avg_soc_t_dep_percent',

]

# Normalise each metric manually
normalised = pd.DataFrame(index=df.index)

for col in lower_better:
    min_val = df[col].min()
    max_val = df[col].max()
    normalised[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 0

for col in higher_better:
    min_val = df[col].min()
    max_val = df[col].max()
    normalised[col] = (max_val - df[col]) / (max_val - min_val) if max_val != min_val else 0

print(normalised.head())

