import pandas as pd

from src.visualisation.datasets.objective_comparison_dataset import (
    build_objective_dso_metrics_df,
    build_objective_economic_metrics_df,
    build_objective_fairness_df,
    build_objective_soc_summary_df,
    build_strategy_fairness_df,
)
from src.visualisation.datasets.technical_dataset import build_technical_summary_df


HEATMAP_COLUMN_ORDER = [
    'Num CP',
    'Rated power',
    'Peak increase',
    'Peak-to-average',
    'Average SOC',
    'Lowest SOC',
    'G coefficient',
]

HEATMAP_UNITS = {
    'Num CP': 'CP',
    'Rated power': 'kW',
    'Peak increase': '%',
    'Peak-to-average': '',
    'Average SOC': '%',
    'Lowest SOC': '%',
    'G coefficient': '',
}

HEATMAP_HIGHER_IS_BETTER = {
    'Num CP': False,
    'Rated power': False,
    'Peak increase': False,
    'Peak-to-average': False,
    'Average SOC': True,
    'Lowest SOC': True,
    'G coefficient': False,
}

HEATMAP_FORMATTERS = {
    'Num CP': '{:.0f}',
    'G coefficient': '{:.3f}',
}


def build_objective_heatmap_df(
        configurations: list[str],
        charging_strategies: list[str],
        versions: list[str],
) -> pd.DataFrame:
    df_econ = build_objective_economic_metrics_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        versions=versions,
    )

    df_dso = build_objective_dso_metrics_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        versions=versions,
    )

    df_soc = build_objective_soc_summary_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        versions=versions,
    )

    df_fairness = build_objective_fairness_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        versions=versions,
    )

    df = (
        df_econ[['version', 'version_label', 'avg_num_cp', 'avg_p_cp_rated']]
        .merge(
            df_dso[['version', 'avg_p_peak_increase', 'avg_papr']],
            on='version',
        )
        .merge(
            df_soc[['version', 'soc_avg', 'lowest_soc']],
            on='version',
        )
        .merge(
            df_fairness[['version', 'gini_coeff']],
            on='version',
        )
        .rename(columns={
            'version_label': 'Objective',
            'avg_num_cp': 'Num CP',
            'avg_p_cp_rated': 'Rated power',
            'avg_p_peak_increase': 'Peak increase',
            'avg_papr': 'Peak-to-average',
            'soc_avg': 'Average SOC',
            'lowest_soc': 'Lowest SOC',
            'gini_coeff': 'G coefficient',
        })
        .set_index('Objective')
    )

    return df[HEATMAP_COLUMN_ORDER]


def build_config_strategy_heatmap_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    df_summary = build_technical_summary_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
    )

    df_fairness = build_strategy_fairness_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
    )

    df = (
        df_summary.merge(
            df_fairness[['config', 'strategy', 'gini_coeff']],
            on=['config', 'strategy'],
        )
        .assign(
            scenario=lambda x: (
                    x['config']
                    .str.replace('Configuration', 'Config', regex=False)
                    + ' | ' +
                    x['strategy']
                    .str.replace('Opportunistic', 'Opp', regex=False)
                    .str.replace('Flexible', 'Flex', regex=False)
            )
        )
        .rename(columns={
            'scenario': 'Scenario',
            'num_cp': 'Num CP',
            'p_cp_rated': 'Rated power',
            'p_peak_increase': 'Peak increase',
            'papr': 'Peak-to-average',
            'avg_soc_t_dep_percent': 'Average SOC',
            'lowest_soc': 'Lowest SOC',
            'gini_coeff': 'G coefficient',
        })
        .set_index('Scenario')
    )

    return df[HEATMAP_COLUMN_ORDER]