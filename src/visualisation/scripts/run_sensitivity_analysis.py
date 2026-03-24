import pandas as pd

from src.visualisation.datasets.sensitivity_analysis_dataset import build_sensitivity_df
from src.visualisation.plots.sensitivity_analysis_plot import plot_sensitivity


def main() -> None:
    pd.set_option('display.max_columns', None)

    version = 'balanced'
    params_combination = [
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 25},  # Baseline
        {'min_soc': 0.2, 'max_soc': 0.4, 'cap': '35_60', 'avg_dist': 25},  # SOC init
        {'min_soc': 0.6, 'max_soc': 0.8, 'cap': '35_60', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '30_40', 'avg_dist': 25},  # Battery capacity
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '55_65', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 15},  # Avg travel distance
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 35},
    ]

    metrics = [
        'num_cp',
        'papr',
        'avg_soc_t_dep_percent',
        'lowest_soc',
    ]

    y_labels = {
        'num_cp': 'Number of charging points',
        'papr': 'Peak-to-average power ratio',
        'avg_soc_t_dep_percent': 'Average SOC at departure (%)',
        'lowest_soc': 'Lowest SOC at departure (%)',
    }

    df_all = build_sensitivity_df(version, params_combination)
    print(df_all)

    df_soc = df_all[df_all['capacity'] == '35-60 kWh']
    df_soc = df_soc[df_soc['distance'] == '25 km']
    # plot_sensitivity(
    #     df_soc,
    #     metrics,
    #     y_labels,
    #     'soc_range',
    #     'Sensitivity to initial SOC range',
    #     'soc_sensitivity.png',
    #     ['20-40%', '40-60%', '60-80%'],
    # )

    df_cap = df_all[df_all['soc_range'] == '40-60%']
    df_cap = df_cap[df_cap['distance'] == '25 km']
    # plot_sensitivity(
    #     df_cap,
    #     metrics,
    #     y_labels,
    #     'capacity',
    #     'Sensitivity to EV battery capacity',
    #     'capacity_sensitivity.png',
    #     ['30-40 kWh', '35-60 kWh', '55-65 kWh'],
    # )

    df_dist = df_all[df_all['soc_range'] == '40-60%']
    df_dist = df_dist[df_dist['capacity'] == '35-60 kWh']
    # plot_sensitivity(
    #     df_dist,
    #     metrics,
    #     y_labels,
    #     'distance',
    #     'Sensitivity to average travel distance',
    #     'distance_sensitivity.png',
    #     ['15 km', '25 km', '35 km'],
    # )


if __name__ == '__main__':
    main()