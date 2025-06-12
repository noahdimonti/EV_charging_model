from src.config import params
from src.models.results.model_results import ModelResults
from src.models.simulations.simulation_model import simulate_and_process
from src.models.utils.log_model_info import log_with_runtime, print_runtime
from src.models.utils.mapping import validate_config_strategy, config_map, strategy_map


def run_simulation_model(
        config: str,
        charging_strategy: str,
        version: str,
        config_attribute: dict[str, int | float | dict[int, list]]) -> ModelResults:
    # Validate config and charging strategy
    validate_config_strategy(config, charging_strategy)

    # Define labels
    label = f'Running simulation for {config}_{charging_strategy}_{params.num_of_evs}EVs model'
    finished_label = 'Simulation finished'

    try:
        simulation_results, simulation_time = log_with_runtime(
            label,
            simulate_and_process,
            config,
            config_attribute
        )

        print_runtime(finished_label, simulation_time)

        # Save results
        results = ModelResults(simulation_results, config_map[config], strategy_map[charging_strategy])
        results.save_model_to_pickle(version=version)

        return results

    except Exception as e:
        print(f'{params.RED}An error occurred: {e}.{params.RESET}')

