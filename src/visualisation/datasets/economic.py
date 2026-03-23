import pandas as pd

from src.config import params
from src.visualisation import io
from src.visualisation.labels import (
    format_config_label,
    format_strategy_label,
)


def build_num_cp_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)

            if config == 'config_1':
                num_cp = params.num_of_evs
            else:
                num_cp = int(model_results.variables['num_cp'])

            p_cp_rated = (
                model_results.variables['p_cp_rated']
                * params.charging_power_resolution_factor
            )

            rows.append({
                'config': format_config_label(config),
                'strategy': format_strategy_label(strategy),
                'model': f'{format_config_label(config)} - {format_strategy_label(strategy)} Charging',
                'num_cp': num_cp,
                'p_cp_rated': p_cp_rated,
            })

    return pd.DataFrame(rows)