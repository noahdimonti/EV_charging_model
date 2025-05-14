import time
from src.config import params
from src.models.mapping import config_map, strategy_map
from src.models.configs import CPConfig, ChargingStrategy
from src.models.simulations.uncoordinated_model import simulate_uncoordinated_model, process_model_results


def run_simulation_model(config: str, charging_strategy: str, p_cp_rated: float, num_cp: int):
    print(f'\n=============================================================\n'
          f'Running simulation for {config}_{charging_strategy}_{params.num_of_evs}EVs model ...'
          f'\n=============================================================')

    try:
        # Simulate model and calculate simulation time
        start_time = time.time()

        model = simulate_uncoordinated_model(p_cp_rated, config, num_cp)
        results = process_model_results(model, p_cp_rated)

        end_time = time.time()

        # Simulation time
        simulation_time = end_time - start_time

        if (simulation_time % 60) < 1:
            print(f'\n{params.GREEN}Simulation finished in {simulation_time:.3f} seconds{params.RESET}')
        else:
            minutes = int(simulation_time // 60)
            remaining_seconds = simulation_time % 60
            print(
                f'\n{params.GREEN}Simulation finished in {minutes} minutes {remaining_seconds:.3f} seconds{params.RESET}')

        print(f'\n-------------------------------------------------------------\n')

        return results

    except Exception as e:
        print(f'{params.RED}An error occurred: {e}.{params.RESET}')
