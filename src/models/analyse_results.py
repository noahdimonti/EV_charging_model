import pandas as pd
import pickle
from src.utils.evaluation_metrics import EvaluationMetrics
from src.utils.model_results import compile_multiple_models_metrics

pd.set_option('display.max_columns', None)
# res = pd.read_csv('../../reports/compiled_metrics.csv')
# print(res)

configurations = [
        'config_1',
        'config_2',
        'config_3',
    ]
charging_strategies = [
        'opportunistic',
        'flexible',
    ]

models_metrics = {}

for config in configurations:
    for strategy in charging_strategies:
        with open(f'../../reports/pkl/{config}_{strategy}_10EVs_7days.pkl', 'rb') as f:
            results = pickle.load(f)

        # Compute evaluation metrics
        metrics = EvaluationMetrics(results)
        metrics.pprint()
        formatted_metrics = metrics.format_metrics()

        # Collect metrics
        models_metrics[f'{config}_{strategy}'] = formatted_metrics

# Compile models metrics
results_df = compile_multiple_models_metrics(models_metrics, filename='compiled_metrics_rev.csv')
print(results_df)

# Plot results
# plot_p_ev(results)
# plot_agg_p_ev(results)
# plot_agg_total_demand(results)
#
# if charging_strategy == 'flexible':
#     plot_ev_charging_schedule(results)