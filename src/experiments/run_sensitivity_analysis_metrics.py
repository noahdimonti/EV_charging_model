import pandas as pd
import os
from src.config import params
from src.config.params import num_of_days
from src.pipelines.analyse_results import analyse_one_model_from_file


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
        df = analyse_one_model_from_file(config, strategy, version)

        print(f'\nVersion: {version}')
        print(df)

        # Save df
        filename = f'raw_values_metrics_{params.num_of_evs}EVs_{num_of_days}days_{version}.csv'
        filepath = os.path.join(params.sensitivity_analysis_res_path, filename)

        df.to_csv(filepath)
        print(f'Metrics successfully saved to {filepath}')



if __name__ == '__main__':
    main()