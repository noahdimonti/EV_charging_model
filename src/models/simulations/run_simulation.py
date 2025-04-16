import time
from src.config import params
from src.models.configs import CPConfig, ChargingStrategy
from src.models.simulations.uncoordinated_charging_config_1 import simulate_model, process_model_results


def run_simulation_model(config: CPConfig, charging_strategy: ChargingStrategy, p_cp_rated: float):
    print(f'\n=========================================================\n'
          f'Running simulation for {config.value}_{charging_strategy.value}_{params.num_of_evs}EVs model ...'
          f'\n=========================================================')

    # Simulate model and calculate simulation time
    start_time = time.time()

    try:
        model = simulate_model(p_cp_rated)
        results = process_model_results(model, p_cp_rated)

    except Exception as e:
        print(f'{params.RED}An error occurred: {e}.{params.RESET}')

    end_time = time.time()

    # Simulation time
    simulation_time = end_time - start_time

    if (simulation_time % 60) < 1:
        print(f'\n{params.GREEN}Simulation finished in {simulation_time:.3f} seconds{params.RESET}')
    else:
        minutes = int(simulation_time // 60)
        remaining_seconds = simulation_time % 60
        print(f'\n{params.GREEN}Simulation finished in {minutes} minutes {remaining_seconds:.3f} seconds{params.RESET}')

    print(f'\n---------------------------------------------------------\n')

    return results
