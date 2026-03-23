import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params
from src.models.results.model_results import EvaluationMetrics
from src.visualisation import io, style, style_helpers
from src.visualisation.labels import format_config_label, format_strategy_label, format_version_label
from pprint import pprint



def build_dso_metrics_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)
            evaluation_metrics = EvaluationMetrics(model_results)

            rows.append({
                'config': format_config_label(config),
                'strategy': format_strategy_label(strategy),
                'p_peak_increase': evaluation_metrics.metrics['p_peak_increase'],
                'papr': evaluation_metrics.metrics['papr'],
            })

    return pd.DataFrame(rows)


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

                p_peak_increase_values.append(evaluation_metrics.metrics['p_peak_increase'])
                papr_values.append(evaluation_metrics.metrics['papr'])

        rows.append({
            'version': format_version_label(version),
            'avg_p_peak_increase': np.mean(p_peak_increase_values),
            'avg_papr': np.mean(papr_values),
        })

    return pd.DataFrame(rows)


def save_dso_metrics_df(df: pd.DataFrame, filename: str) -> None:
    folder = os.path.join(params.metrics_folder_path, 'dso_metrics')
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, filename)
    df.to_csv(filepath, index=False)


def build_p_ev_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)

            for ev_id in model_results.sets['EV_ID']:
                for time in model_results.sets['TIME']:
                    charging_power = model_results.variables['p_ev'][ev_id, time]

                    if charging_power > 0:
                        rows.append({
                            'config': config,
                            'config_label': format_config_label(config),
                            'strategy': strategy,
                            'strategy_label': format_strategy_label(strategy),
                            'ev_id': ev_id,
                            'time': time,
                            'charging_power': charging_power,
                        })

    return pd.DataFrame(rows)