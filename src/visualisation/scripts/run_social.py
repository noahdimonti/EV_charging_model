import pandas as pd
from src.visualisation.datasets.social_dataset import (
    build_soc_df,
    build_wait_time_df,
    build_wait_time_soc_scatter_df,
    build_num_charging_days_df,
    _build_wait_time_rows
)
from src.visualisation.plots.social_plot import (
    plot_soc_boxplot,
    plot_wait_time_boxplot,
    plot_wait_time_soc_scatter,
    plot_num_charging_days,
)
from src.models.results.model_results import EvaluationMetrics, resolve_ev_data
from src.visualisation.io import load_model_results


def main():
    pd.options.display.max_columns = None
    configurations = [
        'config_1',
        'config_2',
        'config_3'
    ]
    charging_strategies = [
        'uncoordinated',
        'opportunistic',
        'flexible'
    ]
    version = 'balanced'

    df_soc = build_soc_df(configurations, charging_strategies, version)
    plot_soc_boxplot(df_soc, version=version, save_img=True)

    df_wait = build_wait_time_df(configurations, charging_strategies, version)
    plot_wait_time_boxplot(df_wait, version=version, save_img=True, save_csv=True)

    df_wait_soc = build_wait_time_soc_scatter_df(configurations, charging_strategies, version)
    plot_wait_time_soc_scatter(df_wait_soc, version=version, save_img=True, save_csv=True, show_trend=False)

    df_days = build_num_charging_days_df(configurations, charging_strategies, version)
    plot_num_charging_days(df_days, version=version, save_img=True)


if __name__ == '__main__':
    main()