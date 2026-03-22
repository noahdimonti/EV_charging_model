import pandas as pd
from src.pipelines.analyse_results import analyse_multiple_models


def main():
    pd.options.display.max_columns = None

    configurations = [
        'config_1',
        'config_2',
        'config_3',
    ]
    charging_strategies = [
        # 'uncoordinated',
        'opportunistic',
        'flexible',
    ]

    version = 'min_soc'
    save_df = True

    print(
        "-----------------------------------------------------------",
        f"\nRunning Metrics Analysis of Models:",
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