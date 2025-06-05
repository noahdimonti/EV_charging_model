import os

import pandas as pd
from scripts.sensitivity_analysis.sensitivity_analysis_tools import run_sensitivity_analysis, get_holistic_metrics
from scripts.sensitivity_analysis.pareto_front import get_pareto_ranks, parallel_plot_pareto, get_balanced_solution
from src.config import params
from src.models.utils.log_model_info import log_with_runtime, print_runtime


def main():
    pd.set_option('display.max_columns', None)

    step = 0.1
    config = 'config_1'
    strategy = 'opportunistic'
    version = 'sensitivity_analysis'
    verbose = False
    time_limit = 10  # for each run of a model
    mip_gap = 0

    # Pipeline actions
    run = False
    get_pareto = True
    plot = False

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

    if get_pareto:
        # Get raw data from sensitivity analysis file
        sens_filename = f'sensitivity_analysis_{config}_{strategy}_{params.num_of_evs}EVs_{step}step.csv'
        file_path = os.path.join(params.sensitivity_analysis_res_path, sens_filename)
        df = pd.read_csv(file_path)

        # Convert raw data into holistic metrics
        holistic_metrics = get_holistic_metrics(df)

        # Get solution columns and pareto ranks
        solutions = holistic_metrics[['investor_score', 'dso_score', 'user_score']]
        ranks = get_pareto_ranks(solutions)

        # Append pareto ranks to holistic metrics dataframe
        holistic_with_pareto_ranks = holistic_metrics.assign(pareto_rank=ranks).sort_values('pareto_rank')
        print(f'Holistic metrics\n{holistic_with_pareto_ranks}')

        # Save pareto front rank data to csv
        holistic_pareto_filename = f'holistic_metrics_pareto_front_{config}_{strategy}_{params.num_of_evs}EVs_{step}step.csv'
        holistic_pareto_filepath = os.path.join(params.sensitivity_analysis_res_path, holistic_pareto_filename)

        holistic_with_pareto_ranks.to_csv(holistic_pareto_filepath)
        print(f'\nHolistic metrics with pareto rank saved to:\n{holistic_pareto_filepath}')

        best_solution = get_balanced_solution(holistic_with_pareto_ranks)
        print(f'Best solution:\n{best_solution}')

        if plot:
            parallel_plot_pareto(holistic_with_pareto_ranks, config, strategy)


if __name__ == '__main__':
    main()
