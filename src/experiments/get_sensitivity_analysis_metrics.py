import pandas as pd
import os

from src.config import params
from src.models.results.model_results import EvaluationMetrics
from src.pipelines.analyse_results import analyse_multiple_models, load_model


def main():
    pd.options.display.max_columns = None

    config = 'config_2'
    strategy = 'opportunistic'
    params_combination = [
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 25},  # Baseline
        {'min_soc': 0.2, 'max_soc': 0.4, 'cap': '35_60', 'avg_dist': 25},  # SOC init
        {'min_soc': 0.6, 'max_soc': 0.8, 'cap': '35_60', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '30_40', 'avg_dist': 25},  # Battery capacity
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '55_65', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 15},  # Avg travel distance
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 35},
    ]

    for comb in params_combination:
        version = (f'balanced_sens_analysis_'
                   f'avgdist{comb['avg_dist']}km_'
                   f'min{comb['min_soc']}_max{comb['max_soc']}_'
                   f'cap{comb['cap']}')

        print(f'\nVersion: {version}\n')

        results = load_model(config, strategy, version)

        # Instantiate evaluation metrics from results
        evaluation_metrics = EvaluationMetrics(results)

        # Get raw and formatted metrics
        raw_metrics = evaluation_metrics.metrics
        formatted_metrics = evaluation_metrics.format_metrics()

        raw_df = pd.DataFrame.from_dict(raw_metrics, orient='index', columns=['value'])
        formatted_df = pd.DataFrame.from_dict(formatted_metrics, orient='index', columns=['value'])

        raw_metrics_filename = (f'sensitivity_analysis_raw_'
                                f'{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv')
        formatted_filename = (f'sensitivity_analysis_formatted_'
                              f'{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv')

        raw_path = os.path.join(params.sensitivity_analysis_res_path, raw_metrics_filename)
        formatted_path = os.path.join(params.sensitivity_analysis_res_path, formatted_filename)

        # Save df
        try:
            raw_df.to_csv(raw_path)
            formatted_df.to_csv(formatted_path)

            print(f'Metrics df saved to:\n{raw_path}\n{formatted_path}')
        except Exception as e:
            print(f'An error occurred while saving files: {e}')





if __name__ == '__main__':
    main()