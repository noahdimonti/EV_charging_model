import os
import pandas as pd

from src.pipelines.analyse_results import analyse_multiple_models
from src.pipelines.multiple_models_pipeline import run_multiple_models
from src.experiments.obj_weights_map import obj_weights_dict
from src.experiments.solver_settings import solver_settings
from src.experiments.var_setup import (
    obj_weights_type,
    version,
    configurations,
    charging_strategies
)


def main():
    pd.options.display.max_columns = None

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
