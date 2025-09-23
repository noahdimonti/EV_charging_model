import pandas as pd
from src.pipelines.experiments_pipeline.pipeline import run_model_pipeline
from src.utils.argparser import get_parser

def main():
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
    analyse = True
    plot = True
    obj_weights = None

    run_model_pipeline(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
        run_model=False,
        analyse=analyse,
        plot=plot,
        solver_settings=None,
        obj_weights=obj_weights,
        thread_count=None
    )


if __name__ == '__main__':
    main()