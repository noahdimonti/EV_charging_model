import pandas as pd
from src.pipelines.metrics_analysis.analyse_results import analyse_results


def analyse_multiple_models():
    pd.options.display.max_columns = None

    configurations = [
        'config_1',
        'config_2',
        'config_3',
    ]
    charging_strategies = [
        'uncoordinated',
        'opportunistic',
        'flexible',
    ]

    version = 'norm_w_sum'

    print(
        "-----------------------------------------------------------",
        f"Running Metrics Analysis of Models:",
        f"Version: {version}",
        f"Configurations: {configurations}",
        f"Charging strategies: {charging_strategies}"
        "-----------------------------------------------------------"
    )

    raw_metrics, formatted_metrics = analyse_results(
        configurations,
        charging_strategies,
        version
    )
    print(f'\nFormatted Metrics\n{formatted_metrics}')


if __name__ == '__main__':
    main()