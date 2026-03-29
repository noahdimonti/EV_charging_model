import os
import pickle
import glob
from src.config import params
from src.config.ev_params import load_ev_data
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.models.simulation_models.run_simulation import run_simulation_model


def run_multiple_models(configurations: list,
                        charging_strategies: list,
                        version: str,
                        solver_settings: dict,
                        obj_weights: dict[str, int|float] | None = None):

    # Check if version is unique
    for config in configurations:
        for strategy in charging_strategies:
            filename = f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
            filepath = os.path.join(params.model_results_folder_path, filename)
            version_found = os.path.exists(filepath)

            if version_found:
                raise ValueError(f"\nVersion {version} already exists for {config} {strategy}. Please provide a unique version name.")

    ev_data = load_ev_data()

    for config in configurations:
        opt_results_per_config = {}

        # Run optimisation models first
        for strategy in charging_strategies:
            # Skip uncoordinated model
            if strategy == 'uncoordinated':
                continue

            # Set mip_gap, time_limit, and verbose
            model_name = f'{config}_{strategy}'
            mip_gap = solver_settings[model_name][0]
            time_limit = solver_settings[model_name][1]
            verbose = solver_settings[model_name][2]
            thread_count = solver_settings[model_name][3]

            # Run optimisation model
            opt_result = run_optimisation_model(
                config=config,
                charging_strategy=strategy,
                version=version,
                verbose=verbose,
                time_limit=time_limit,
                mip_gap=mip_gap,
                obj_weights=obj_weights,
                thread_count=thread_count,
                ev_data=ev_data
            )

            # Store optimisation model results
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
                config_attribute=config_attr,
                ev_data=ev_data
            )
            opt_results_per_config['uncoordinated'] = simulation_result
