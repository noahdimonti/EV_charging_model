from src.config import params
from src.models.results.model_results import ModelResults
from src.models.simulations.simulation_model import simulate_and_process
from src.models.utils.log_model_info import log_with_runtime, print_runtime
from src.models.utils.mapping import validate_config_strategy, config_map, strategy_map


def run_simulation_model(
        config: str,
        charging_strategy: str,
        version: str,
        obj_weights: dict[str, float],
        config_attribute: dict[str, int | float | dict[int, list]]) -> ModelResults:
    # Validate config and charging strategy
    validate_config_strategy(config, charging_strategy)

    # Define labels
    label = f'Running simulation for {config}_{charging_strategy}_{params.num_of_evs}EVs model'
    finished_label = 'Simulation finished'

    # try:
    simulation_results, simulation_time = log_with_runtime(
        label,
        finished_label,
        simulate_and_process,
        config,
        config_attribute
    )

    print_runtime(finished_label, simulation_time)

    # Save results
    results = ModelResults(simulation_results, config_map[config], strategy_map[charging_strategy], obj_weights)
    results.save_model_to_pickle(version=version)

    return results

    # except Exception as e:
    #     print(f'{params.RED}An error occurred: {e}.{params.RESET}')



# def run_simulation_model(config: str, charging_strategy: str, func, *args, **kwargs):
#     print(f'\n=============================================================\n'
#           f'Running simulation for {config}_{charging_strategy}_{params.num_of_evs}EVs model ...'
#           f'\n=============================================================')
#
#     try:
#         # Simulate model and calculate simulation time
#         start_time = time.time()
#
#         results = func(*args, **kwargs)
#
#         end_time = time.time()
#
#         # Simulation time
#         simulation_time = end_time - start_time
#
#         if (simulation_time % 60) < 1:
#             print(f'\n{params.GREEN}Simulation finished in {simulation_time:.3f} seconds{params.RESET}')
#         else:
#             minutes = int(simulation_time // 60)
#             remaining_seconds = simulation_time % 60
#             print(
#                 f'\n{params.GREEN}Simulation finished in {minutes} minutes {remaining_seconds:.3f} seconds{params.RESET}')
#
#         print(f'\n-------------------------------------------------------------\n')
#
#         return results
#
#     except Exception as e:
#         print(f'{params.RED}An error occurred: {e}.{params.RESET}')
