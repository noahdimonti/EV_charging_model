import pandas as pd
import time
from src.models.configs import CPConfig, ChargingStrategy
from src.config import params, ev_params


def run_simulation_model(config: CPConfig, charging_strategy: ChargingStrategy, p_cp_rated: float):
    print(f'\n=========================================================\n'
          f'Running simulation for {config.value}_{charging_strategy.value} model ...'
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


def simulate_model(p_cp_rated: float):
    # Household load
    household_load = params.household_load

    # Initialise EV data
    ev_data = ev_params.ev_instance_list

    # Set rated power of CP
    p_cp_rated_scaled = p_cp_rated / params.charging_power_resolution_factor

    # Precompute grid capacity constraints to avoid repeated checks
    if (household_load > params.P_grid_max).any().any():
        raise ValueError("Demand is higher than the maximum grid capacity.")

    # Calculate the total number of EVs at time t
    num_ev_at_home_list = []
    for t in params.timestamps:
        num_ev_at_home = sum(
            ev.at_home_status.loc[t].values.item() for ev in ev_data
        )
        num_ev_at_home_list.append({
            'timestamp': t,
            'num_ev_at_home': num_ev_at_home
        })

    num_ev_at_home_df = pd.DataFrame(num_ev_at_home_list).set_index('timestamp')

    # Iterate over EVs
    for i, ev in enumerate(ev_data):
        # Initialise charging power and soc empty list
        p_ev = []
        soc_ev = []

        for t in params.timestamps:
            # Calculate CCP max capacity
            ccp_capacity = params.P_grid_max - household_load.loc[t].values.item()

            # calculate maximum charging power per EV divided evenly
            available_power_at_cp = (ccp_capacity / num_ev_at_home_df.loc[t].values.item()) \
                if num_ev_at_home_df.loc[t].values > 1 else ccp_capacity

            # Assign charging power and SOC according to constraints
            if t == params.start_date_time:
                # Assign initial charging power and soc
                p_ev.append(0)
                soc_ev.append(ev.soc_init)
            else:
                if ev.at_home_status.loc[t].values == 0:
                    # EV is NOT at home: charging power is 0 and soc remains unchanged
                    p_ev.append(0)
                    soc_ev.append(soc_ev[-1])
                else:
                    # EV is at home: calculate charging power and soc
                    available_power = min(available_power_at_cp, p_cp_rated_scaled)

                    # Subtract travel energy if t is at arrival time
                    if t in ev.t_arr:
                        k = ev_params.t_arr_dict[i].index(t)
                        soc_ev[-1] -= ev.travel_energy[k]

                    # Predict SOC based on available charging power
                    potential_soc = soc_ev[-1] + available_power

                    if potential_soc > ev.soc_max:
                        # Calculate how much energy is needed to reach SOC max
                        remaining_to_charge = ev.soc_max - soc_ev[-1]
                        p_ev.append(remaining_to_charge)
                        soc_ev.append(ev.soc_max)
                    else:
                        # Assign available power to charging power and SOC accordingly
                        p_ev.append(available_power)
                        soc_ev.append(potential_soc)

        # Assign charging power and soc list to dataframes in EV object
        ev.charging_power['charging_power'] = p_ev
        ev.soc['soc'] = soc_ev

    return ev_data


def process_model_results(model: list, p_cp_rated: float):
    household_load = params.household_load

    all_results = {
        'p_grid': {},
        'p_cp_rated': p_cp_rated,
        'p_ev': {},
        'soc_ev': {},
    }

    for i, ev in enumerate(model):
        for t in params.timestamps:
            # Extract p_grid
            all_results['p_grid'][t] = household_load.loc[t].values.item() + sum(e.charging_power.loc[t].values.item() for e in model)

            # Extract charging power
            all_results['p_ev'][(i, t)] = ev.charging_power.loc[t].values.item()

            # Extract SOC
            all_results['soc_ev'][(i, t)] = ev.soc.loc[t].values.item()

    return all_results








