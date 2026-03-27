import os
import pandas as pd
from src.pipelines.analyse_results import analyse_multiple_models
from src.experiments.var_setup import (
    obj_weights_type,
    version,
    configurations,
    charging_strategies
)


def main():
    pd.options.display.max_columns = None

    save_df = False

    print(
        "-----------------------------------------------------------",
        f"\nRunning Metrics Analysis of Models:",
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
        save_df
    )

    print(f'\nFormatted Metrics\n{formatted_metrics}')


if __name__ == '__main__':
    main()