from scripts.execute_models import execute_model
from scripts.analyse_results import analyse_results
from src.config import params
from src.visualisation import plot_models_comparison
from pprint import pprint


def main():
    version = 'confpaper_complete_obj'

    configurations = [
        'config_1',
        # 'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        # 'uncoordinated',
        # 'opportunistic',
        'flexible',
    ]

    # Mapping for mip_gap, time_limit, and verbose for each model
    solver_settings = {  # { model_name: [mip_gap, time_limit, verbose] }
        'config_1_uncoordinated': [None, None, False],
        'config_1_opportunistic': [None, None, False],
        'config_1_flexible': [0.5, 5, True],
        'config_2_uncoordinated': [],
        'config_2_opportunistic': [],
        'config_2_flexible': [],
        'config_3_uncoordinated': [],
        'config_3_opportunistic': [],
        'config_3_flexible': [],
    }

    # Actions in pipeline
    run_model = True
    analyse = False
    plot = False

    # Execute model, analyse, and plot
    run_pipeline(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
        run_model=run_model,
        solver_settings=solver_settings,
        analyse=analyse,
        plot=plot
    )


def run_pipeline(configurations: list,
                 charging_strategies: list,
                 version: str,
                 run_model: bool,
                 solver_settings: dict,
                 analyse: bool,
                 plot: bool):

    if run_model:
        for config in configurations:
            for charging_strategy in charging_strategies:
                # Set mip_gap, time_limit, and verbose
                mip_gap = solver_settings[f'{config}_{charging_strategy}'][0]
                time_limit = solver_settings[f'{config}_{charging_strategy}'][1]
                verbose = solver_settings[f'{config}_{charging_strategy}'][2]

                # Run, solve, and save solved model
                execute_model(
                    config,
                    charging_strategy,
                    version=version,
                    mip_gap=mip_gap,
                    time_limit=time_limit,
                    verbose=verbose
                )

    if analyse:
        raw_metrics, formatted_metrics = analyse_results(
            configurations,
            charging_strategies,
            version,
            params.num_of_evs
        )
        print(formatted_metrics)

    if plot:
        plot_models_comparison.demand_profiles(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )
        plot_models_comparison.soc_distribution(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )
        plot_models_comparison.users_cost_distribution(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )


if __name__ == '__main__':
    main()
