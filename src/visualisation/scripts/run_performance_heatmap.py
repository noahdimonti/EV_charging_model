from src.config import params
from src.visualisation.datasets.performance_heatmap_dataset import (
    HEATMAP_HIGHER_IS_BETTER,
    HEATMAP_UNITS,
    HEATMAP_FORMATTERS,
    build_config_strategy_heatmap_df,
    build_objective_heatmap_df,
)
from src.visualisation.plots.performance_heatmap_plot import plot_performance_heatmap


def main() -> None:
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['opportunistic', 'flexible']
    versions = [
        'min_econ',
        'min_tech',
        'min_soc',
        'econ_tech',
        'tech_soc',
        'econ_soc',
        'balanced',
    ]

    df_objectives = build_objective_heatmap_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        versions=versions,
    )

    plot_performance_heatmap(
        df=df_objectives,
        title='Trade-Offs Between Objective Prioritisation',
        y_label='Objective',
        filename=f'objective_comparison_heatmap_{params.num_of_evs}EVs.png',
        formatters=HEATMAP_FORMATTERS,
        units=HEATMAP_UNITS,
        higher_is_better=HEATMAP_HIGHER_IS_BETTER,
        cmap='YlGnBu',
        save_img=True,
    )

    df_scenarios = build_config_strategy_heatmap_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version='balanced',
    )

    plot_performance_heatmap(
        df=df_scenarios,
        title='Performance Evaluation of Charging Strategies',
        y_label='Scenario',
        filename=f'charging_strategies_heatmap_{params.num_of_evs}EVs.png',
        formatters=HEATMAP_FORMATTERS,
        units=HEATMAP_UNITS,
        higher_is_better=HEATMAP_HIGHER_IS_BETTER,
        cmap='YlOrBr',
        save_img=True,
    )


if __name__ == '__main__':
    main()