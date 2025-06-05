import os
import pickle
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.config import params
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.models.simulations.run_simulation import run_simulation_model
from src.visualisation import plot_models_comparison


def run_model_pipeline(configurations: list,
                       charging_strategies: list,
                       obj_weights: dict,
                       version: str,
                       run_model: bool,
                       solver_settings: dict,
                       analyse: bool,
                       plot: bool):

    if run_model:
        for config in configurations:
            opt_results_per_config = {}

            # Run optimisation models first
            for strategy in charging_strategies:
                # Skip uncoordinated model
                if strategy == 'uncoordinated':
                    continue

                # Set mip_gap, time_limit, and verbose
                mip_gap = solver_settings[f'{config}_{strategy}'][0]
                time_limit = solver_settings[f'{config}_{strategy}'][1]
                verbose = solver_settings[f'{config}_{strategy}'][2]

                opt_result = run_optimisation_model(
                    config=config,
                    charging_strategy=strategy,
                    version=version,
                    obj_weights=obj_weights,
                    verbose=verbose,
                    time_limit=time_limit,
                    mip_gap=mip_gap
                )
                print(f'obj value: {opt_result.objective_value}')

                opt_results_per_config[strategy] = opt_result

            # Run simulation model after getting optimisation model results
            if 'uncoordinated' in charging_strategies:
                # Check if opportunistic model result exists
                root_path = params.model_results_folder_path
                filename = f'{config}_opportunistic_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
                file_path = os.path.join(root_path, filename)

                if 'opportunistic' in opt_results_per_config:
                    config_attr = opt_results_per_config['opportunistic'].get_config_attributes_for_simulation()

                elif os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        opportunistic_model = pickle.load(f)

                    config_attr = opportunistic_model.get_config_attributes_for_simulation()

                else:
                    raise ValueError(f'{params.RED}Missing opportunistic model result for {config}.{params.RESET}')

                simulation_result = run_simulation_model(
                    config=config,
                    charging_strategy='uncoordinated',
                    version=version,
                    obj_weights=obj_weights,
                    config_attribute=config_attr
                )
                opt_results_per_config['uncoordinated'] = simulation_result

    if analyse:
        raw_metrics, formatted_metrics = analyse_results(
            configurations,
            charging_strategies,
            version
        )
        print(f'\nFormatted Metrics\n{formatted_metrics}')

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
