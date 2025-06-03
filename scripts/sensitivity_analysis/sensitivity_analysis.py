import pandas as pd
import numpy as np
import itertools
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.config import params
from src.models.optimisation_models.run_optimisation import run_optimisation_model


# Generate weights that sum to 1
step = 0.1
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
analyse = False
filename = f'{params.project_root}/data/outputs/metrics/sensitivity_analysis_{step}step.csv'

if analyse:
    df = pd.DataFrame()

    for weights in weight_dicts:
        print(f'\nObjective weights: {weights}')

        # Run model and analyse results
        run_optimisation_model(
            config=config,
            charging_strategy=strategy,
            version=version,
            obj_weights=weights
        )
        raw, formatted = analyse_results([config], [strategy], version)

        # Store results in a dataframe
        df = pd.concat([raw, df], axis=1)

    df = df.T  # Transpose so each row is one config
    df.to_csv(filename)


# Normalise metrics
def normalise_metrics(df):
    df = df.drop('Unnamed: 0', axis=1)
    normalised = pd.DataFrame(index=df.index)
    for col in df.columns:
        min_val = df[col].min()
        max_val = df[col].max()
        normalised[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 0

    return normalised


pd.set_option('display.max_columns', None)
df = pd.read_csv(filename)
# print(df)

normalised = normalise_metrics(df)
# print(normalised)

# Create holistic score dataframe
holistic_metrics = pd.DataFrame(columns=['investor_score', 'dso_score', 'user_score'])
holistic_metrics = pd.concat([holistic_metrics, normalised[['economic', 'technical', 'social']]], axis=1)
holistic_metrics.rename(columns={
    'economic': 'economic_weight',
    'technical': 'technical_weight',
    'social': 'social_weight'
}, inplace=True)

# Economic score
holistic_metrics['investor_score'] = 1 - normalised['investment_cost']

# Technical score
holistic_metrics['dso_score'] = ((1 - normalised['avg_p_peak']) *
                                       (1 - normalised['avg_papr']) *
                                       (1 - normalised['avg_daily_peak_increase']))

# Social score - NOT FINALISED
holistic_metrics['user_score'] = ((1 - normalised['total_cost_per_user']) *  # cost component
                                    (normalised['avg_soc_t_dep_percent']) *  # how much SOC
                                    (1 - normalised['soc_range']))  # fairness

print(holistic_metrics)



