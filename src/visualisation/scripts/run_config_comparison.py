import os

import numpy as np
import pandas as pd

from src.config import params
from src.models.results.model_results import EvaluationMetrics, resolve_ev_data
from src.visualisation import io
from src.visualisation.datasets.objective_comparison_dataset import calculate_gini


def build_uncoordinated_config_comparison_df(
        configurations: list[str],
        version: str,
) -> pd.DataFrame:
    strategy = 'uncoordinated'
    rows = []

    for config in configurations:
        model_results = io.load_model_results(config, strategy, version)
        evaluation_metrics = EvaluationMetrics(model_results)
        ev_data = resolve_ev_data(model_results)

        soc_t_dep_values = np.array([
            (model_results.variables['soc_ev'][ev_id, time] / ev_data.soc_max_dict[ev_id]) * 100
            for ev_id in model_results.sets['EV_ID']
            for time in ev_data.t_dep_dict[ev_id]
        ])

        rows.append({
            'config': int(config.split('_')[-1]),
            'num_cp': int(evaluation_metrics.metrics['num_cp']),
            'p_cp_rated': evaluation_metrics.metrics['p_cp_rated'],
            'p_peak_increase': evaluation_metrics.metrics['p_peak_increase'],
            'papr': evaluation_metrics.metrics['papr'],
            'avg_soc_t_dep_percent': evaluation_metrics.metrics['avg_soc_t_dep_percent'],
            'lowest_soc': evaluation_metrics.metrics['lowest_soc'],
            'gini_coefficient': calculate_gini(soc_t_dep_values),
        })

    df = pd.DataFrame(rows).sort_values('config').reset_index(drop=True)

    return df


def format_uncoordinated_config_comparison_df(df: pd.DataFrame) -> pd.DataFrame:
    formatted_df = df.copy()

    formatted_df['config'] = formatted_df['config'].astype(int).astype(str)
    formatted_df['num_cp'] = formatted_df['num_cp'].astype(int)
    formatted_df['p_cp_rated'] = formatted_df['p_cp_rated'].map(lambda value: f'{value:.2f} kW')
    formatted_df['p_peak_increase'] = formatted_df['p_peak_increase'].map(lambda value: f'{value:.2f}%')
    formatted_df['papr'] = formatted_df['papr'].map(lambda value: f'{value:.4f}')
    formatted_df['avg_soc_t_dep_percent'] = formatted_df['avg_soc_t_dep_percent'].map(lambda value: f'{value:.2f}%')
    formatted_df['lowest_soc'] = formatted_df['lowest_soc'].map(lambda value: f'{value:.2f}%')
    formatted_df['gini_coefficient'] = formatted_df['gini_coefficient'].map(lambda value: f'{value:.4f}')

    return formatted_df


def main():
    configurations = [
        'config_1',
        'config_2',
        'config_3'
    ]
    version = 'balanced'

    df_raw = build_uncoordinated_config_comparison_df(
        configurations=configurations,
        version=version,
    )
    df_table = format_uncoordinated_config_comparison_df(df_raw)

    filename = os.path.join(params.metrics_folder_path, f'config_comparison_table_{version}.csv')
    df_table.to_csv(filename)

    print(df_table.to_string(index=False))


if __name__ == '__main__':
    main()
