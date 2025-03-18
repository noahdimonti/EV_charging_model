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
        with open(f'../../reports/{config}_{strategy}_10EVs_7days.pkl', 'rb') as f:
            results = pickle.load(f)

        # Compute evaluation metrics
        metrics = EvaluationMetrics(results)
        metrics.pprint()
        formatted_metrics = metrics.format_metrics()

        # Collect metrics
        models_metrics[f'{config}_{strategy}'] = formatted_metrics

# Compile models metrics
results_df = compile_multiple_models_metrics(models_metrics, filename='compiled_metrics.csv')
print(results_df)