import os
import pandas as pd

from src.pipelines.analyse_results import analyse_multiple_models
from src.pipelines.multiple_models_pipeline import run_multiple_models
from src.experiments.obj_weights_map import obj_weights_dict
from src.experiments.var_setup import (
    obj_weights_type,
    version,
    configurations,
    charging_strategies
)


def main():
    pd.options.display.max_columns = None

    # Mapping for mip_gap, time_limit, and verbose for each model
    solver_settings = {  # { model_name: [mip_gap (%), time_limit (minute), verbose, num threads] }
        'config_1_uncoordinated': [None, None, False, 8],
        'config_1_opportunistic': [1, 120, True, 16],
        'config_1_flexible': [1, 240, True, 16],

        'config_2_uncoordinated': [None, None, False, 8],
        'config_2_opportunistic': [2.8778, 360, True, 32],
        'config_2_flexible': [3, 360, True, 32],

        'config_3_uncoordinated': [None, None, False, 8],
        'config_3_opportunistic': [5, 360, True, 32],
        'config_3_flexible': [5, 720, True, 32],
    }

    save_metrics_df = False


    print(
        "-----------------------------------------------------------",
        f"\nRunning Model(s):",
        f"\nPID: {os.getpid()}"
        f"\nObjective Weights Type: {obj_weights_type}",
        f"\nVersion: {version}",
        f"\nConfigurations: {configurations}",
        f"\nCharging strategies: {charging_strategies}"
        "\n-----------------------------------------------------------"
    )

    obj_weights = obj_weights_dict[obj_weights_type]

    run_multiple_models(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
        obj_weights=obj_weights,
        solver_settings=solver_settings,
    )

    print(
        "-----------------------------------------------------------",
        f"\nRunning Metrics Analysis:",
        f"\nPID: {os.getpid()}"
        f"\nObjective Weights Type: {obj_weights_type}",
        f"\nVersion: {version}",
        f"\nConfigurations: {configurations}",
        f"\nCharging strategies: {charging_strategies}"
        "\n-----------------------------------------------------------"
    )

    raw_metrics, formatted_metrics = analyse_multiple_models(
        configurations,
        charging_strategies,
        version,
        save_metrics_df
    )

    print(f'\nFormatted Metrics\n{formatted_metrics}')



if __name__ == '__main__':
    main()
