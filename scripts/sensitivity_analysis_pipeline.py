import os

import pandas as pd
from scripts.sensitivity_analysis.sensitivity_analysis_tools import run_sensitivity_analysis, get_holistic_metrics
from scripts.sensitivity_analysis.pareto_front import get_pareto_front_indices, get_pareto_ranks, parallel_plot_pareto
from src.config import params
from src.models.utils.log_model_info import log_with_runtime, print_runtime


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
    run = False
    get_metrics = True
    get_pareto = True

    if run:
        label = f'Running sensitivity analysis with {step} step'
        finished_label = f'Sensitivity analysis carried out'

        result, runtime = log_with_runtime(
            label,
            run_sensitivity_analysis,
            step,
            config,
            strategy,
            version,
            verbose,
            time_limit,
            mip_gap
        )

        print_runtime(finished_label, runtime)

    if get_metrics:
        file_path = os.path.join(params.sensitivity_analysis_res_path,
                                 f'sensitivity_analysis_{config}_{strategy}_{params.num_of_evs}EVs_{step}step.csv')
        df = pd.read_csv(file_path)
        holistic_metrics = get_holistic_metrics(df)

        print(f'\nHolistic metrics:\n{holistic_metrics}')

        if get_pareto:
            solutions = holistic_metrics[['investor_score', 'dso_score', 'user_score']]

            pareto_idxs = get_pareto_front_indices(solutions)

            print("Pareto front indices:", pareto_idxs)
            print("Pareto-optimal rows:\n", holistic_metrics.loc[pareto_idxs])

            ranks = get_pareto_ranks(solutions)

            final_df = holistic_metrics.assign(pareto_rank=ranks).sort_values('pareto_rank')
            print('final_df')
            print(final_df)

            pareto_front_filename = f'{params.project_root}/data/outputs/metrics/pareto_front_{step}step.csv'

            final_df.to_csv(pareto_front_filename)
            print(f'Saved pareto front file to:\n{pareto_front_filename}')

            parallel_plot_pareto(final_df)


if __name__ == '__main__':
    main()
