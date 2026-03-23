from src.visualisation.datasets.objective_comparison_dataset import (
    build_objective_dso_metrics_df,
    build_objective_economic_metrics_df,
    build_objective_fairness_df,
    build_objective_soc_df,
    build_objective_soc_summary_df,
    build_objective_wait_time_df,
    build_strategy_fairness_df,
)
from src.visualisation.plots.objective_comparison_plot import (
    plot_objective_soc_boxplot,
    plot_objective_wait_time_boxplot,
)


def main() -> None:
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['opportunistic', 'flexible']
    versions = [
        'min_econ',
        'min_tech',
        'econ_tech',
        'balanced',
    ]

    df_soc = build_objective_soc_df(configurations, charging_strategies, versions)
    df_soc_summary = build_objective_soc_summary_df(
        configurations,
        charging_strategies,
        versions,
    )
    df_dso = build_objective_dso_metrics_df(
        configurations,
        charging_strategies,
        versions,
    )
    df_economic = build_objective_economic_metrics_df(
        configurations,
        charging_strategies,
        versions,
    )
    df_wait_time = build_objective_wait_time_df(
        configurations,
        charging_strategies,
        versions,
    )
    df_fairness = build_objective_fairness_df(
        configurations,
        charging_strategies,
        versions,
    )
    df_strategy_fairness = build_strategy_fairness_df(
        configurations,
        charging_strategies,
        version='balanced',
    )

    print(df_soc_summary)
    print(df_dso)
    print(df_economic)
    print(df_fairness)
    print(df_strategy_fairness)

    plot_objective_soc_boxplot(df_soc, save_img=True)
    plot_objective_wait_time_boxplot(df_wait_time, save_img=True)


if __name__ == '__main__':
    main()