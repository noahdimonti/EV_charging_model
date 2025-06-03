import pandas as pd
from sensitivity_analysis_tools import run_sensitivity_analysis, get_holistic_metrics
from src.config import params


def main():
    pd.set_option('display.max_columns', None)

    step = 0.5
    config = 'config_1'
    strategy = 'opportunistic'
    version = 'sensitivity_analysis'
    verbose = False
    time_limit = 10
    mip_gap = 0

    # Pipeline actions
    run = True
    get_metrics = True

    if run:
        df = run_sensitivity_analysis(
            step=step,
            config=config,
            strategy=strategy,
            version=version,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap
        )
    print(df)

    if get_metrics:
        holistic_metrics = get_holistic_metrics(df)
        print(holistic_metrics)




if __name__ == '__main__':
    main()
