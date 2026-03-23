import os
import pandas as pd

from src.config import params


def get_filepath(version: str, min_soc: float, max_soc: float, cap: str, avg_dist: int) -> str:
    file_prefix = f'raw_values_compiled_metrics_{params.num_of_evs}EVs_{params.num_of_days}days_{version}'
    file_parameters = f'{min_soc}min_{max_soc}max_cap{cap}_{avg_dist}km.csv'
    file_path = '_'.join([file_prefix, file_parameters])

    return file_path


def build_sensitivity_df(version: str, params_comb: list[dict]) -> pd.DataFrame:
    all_data = []

    folder = os.path.join(params.compiled_metrics_folder_path, 'sensitivity_analysis')

    metrics_keep = [
        'num_cp',
        'p_cp_rated',
        'p_peak_increase',
        'papr',
        'avg_soc_t_dep_percent',
        'lowest_soc',
    ]

    for parameter in params_comb:
        filepath = get_filepath(
            version,
            parameter['min_soc'],
            parameter['max_soc'],
            parameter['cap'],
            parameter['avg_dist'],
        )
        file = os.path.join(folder, filepath)

        df = pd.read_csv(file, index_col=0).T
        df = df[metrics_keep]

        df['model_case'] = filepath.replace('.csv', '')
        all_data.append(df)

    df_all = pd.concat(all_data, ignore_index=True)

    soc_vals = df_all['model_case'].str.extract(r'(\d\.\d)min_(\d\.\d)max')

    df_all['soc_range'] = (
        (soc_vals[0].astype(float) * 100).astype(int).astype(str)
        + '-'
        + (soc_vals[1].astype(float) * 100).astype(int).astype(str)
        + '%'
    )

    df_all['capacity'] = (
        df_all['model_case']
        .str.extract(r'cap(\d+-\d+)')[0]
        + ' kWh'
    )

    df_all['distance'] = (
        df_all['model_case']
        .str.extract(r'(\d+)km')[0]
        + ' km'
    )

    df_all = df_all[
        [
            'model_case',
            'soc_range',
            'capacity',
            'distance',
            'p_peak_increase',
            'papr',
            'num_cp',
            'p_cp_rated',
            'avg_soc_t_dep_percent',
            'lowest_soc',
        ]
    ]

    df_all = df_all.set_index('model_case')

    return df_all