from scripts.experiments_pipeline.execute_models import execute_model
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.config import params, independent_variables
from src.visualisation import plot_models_comparison


def main():
    configurations = [
        # 'config_1',
        # 'config_2',
        'config_3',
    ]
    charging_strategies = [
        # 'uncoordinated',
        'opportunistic',
        # 'flexible',
    ]

    # Objective weights
    obj_weights = {
        'economic': 0.3,
        'technical': 0.4,
        'social': 0.4
    }

    # Number of CP for uncoordinated strategy
    num_cp = params.num_of_evs

    # Actions in pipeline
    version = 'test_conf3_bug_solved'
    run_model = True
    analyse = False
    plot = False

    # Mapping for mip_gap, time_limit, and verbose for each model
    solver_settings = {  # { model_name: [mip_gap (%), time_limit (minute), verbose] }
        'config_1_uncoordinated': [None, None, False],
        'config_1_opportunistic': [None, None, False],
        'config_1_flexible': [0.1, 25, False],

        'config_2_uncoordinated': [],
        'config_2_opportunistic': [0.9, 25, True],
        'config_2_flexible': [0.9, 30, True],

        'config_3_uncoordinated': [],
        'config_3_opportunistic': [0.9, 25, True],
        'config_3_flexible': [0.9, 30, True],
    }

    # Execute model, analyse, and plot
    run_pipeline(
        configurations=configurations,
        charging_strategies=charging_strategies,
        num_cp=num_cp,
        obj_weights=obj_weights,
        version=version,
        run_model=run_model,
        solver_settings=solver_settings,
        analyse=analyse,
        plot=plot
    )


def run_pipeline(configurations: list,
                 charging_strategies: list,
                 num_cp: int,
                 obj_weights: dict,
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
                    num_cp=num_cp,
                    obj_weights=obj_weights,
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
            num_cp
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
