import pandas as pd
import numpy as np

from src.models.results.model_results import EvaluationMetrics
from src.visualisation import io
from src.visualisation.datasets.social_dataset import (
    build_soc_df,
    build_wait_time_df,
)
from src.visualisation.labels import (
    format_config_label,
    format_strategy_label,
    format_version_label,
)


def build_objective_soc_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    rows = []

    for version in versions:
        df_soc = build_soc_df(configurations, charging_strategies, version).copy()
        df_soc['version'] = version
        df_soc['version_label'] = format_version_label(version)
        rows.append(df_soc)

    return pd.concat(rows, ignore_index=True)


def build_objective_soc_summary_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    df = build_objective_soc_df(configurations, charging_strategies, versions)

    summary = (
        df.groupby(['version', 'version_label'], as_index=False)['soc_t_dep']
        .agg(
            soc_avg='mean',
            lowest_soc='min',
        )
    )

    return summary


def build_objective_dso_metrics_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    rows = []

    for version in versions:
        p_peak_increase_values = []
        papr_values = []

        for config in configurations:
            for strategy in charging_strategies:
                model_results = io.load_model_results(config, strategy, version)
                evaluation_metrics = EvaluationMetrics(model_results)

                p_peak_increase_values.append(
                    evaluation_metrics.metrics['p_peak_increase']
                )
                papr_values.append(evaluation_metrics.metrics['papr'])

        rows.append({
            'version': version,
            'version_label': format_version_label(version),
            'avg_p_peak_increase': np.mean(p_peak_increase_values),
            'avg_papr': np.mean(papr_values),
        })

    return pd.DataFrame(rows)


def build_objective_economic_metrics_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    rows = []

    for version in versions:
        num_cp_values = []
        p_cp_rated_values = []

        for config in configurations:
            for strategy in charging_strategies:
                model_results = io.load_model_results(config, strategy, version)
                evaluation_metrics = EvaluationMetrics(model_results)

                num_cp_values.append(evaluation_metrics.metrics['num_cp'])
                p_cp_rated_values.append(evaluation_metrics.metrics['p_cp_rated'])

        rows.append({
            'version': version,
            'version_label': format_version_label(version),
            'avg_num_cp': np.mean(num_cp_values),
            'avg_p_cp_rated': np.mean(p_cp_rated_values),
        })

    return pd.DataFrame(rows)


def build_objective_wait_time_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    rows = []

    for version in versions:
        df_wait = build_wait_time_df(configurations, charging_strategies, version).copy()
        df_wait['version'] = version
        df_wait['version_label'] = format_version_label(version)
        rows.append(df_wait)

    return pd.concat(rows, ignore_index=True)


def calculate_gini(values: np.ndarray) -> float:
    values = np.asarray(values).flatten()
    n = len(values)
    mean_value = np.mean(values)

    if mean_value == 0:
        return 0.0

    total_diff_sum = 0.0
    for i in range(n):
        for j in range(n):
            total_diff_sum += abs(values[i] - values[j])

    return total_diff_sum / (2 * (n ** 2) * mean_value)


def build_objective_fairness_df(
    configurations: list[str],
    charging_strategies: list[str],
    versions: list[str],
) -> pd.DataFrame:
    df_soc = build_objective_soc_df(configurations, charging_strategies, versions)

    rows = []
    for version in versions:
        sub = df_soc[df_soc['version'] == version]

        soc_values = sub['soc_t_dep'].to_numpy()

        rows.append({
            'version': version,
            'version_label': format_version_label(version),
            'gini_coeff': round(calculate_gini(soc_values), 4),
        })

    return pd.DataFrame(rows)


def build_strategy_fairness_df(
    configurations: list[str],
    charging_strategies: list[str],
    version: str,
) -> pd.DataFrame:
    df_soc = build_soc_df(configurations, charging_strategies, version)

    rows = []
    for config in configurations:
        for strategy in charging_strategies:
            sub = df_soc[
                (df_soc['config'] == format_config_label(config)) &
                (df_soc['strategy'] == format_strategy_label(strategy))
            ]

            soc_values = sub['soc_t_dep'].to_numpy()

            rows.append({
                'config': format_config_label(config),
                'strategy': format_strategy_label(strategy),
                'gini_coeff': round(calculate_gini(soc_values), 4),
            })

    return pd.DataFrame(rows)