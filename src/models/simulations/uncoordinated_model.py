import pandas as pd
from src.config import params, ev_params
from src.models.simulations import config_1, config_2


def simulate_uncoordinated_model(p_cp_rated: float, config: str, num_cp: int):
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

    simulated_data = None

    if config == 'config_1':
        simulated_data = config_1.uncoordinated_model_config_1(
            ev_data,
            household_load,
            num_ev_at_home_df,
            p_cp_rated_scaled
        )
    elif config == 'config_2':
        simulated_data = config_2.uncoordinated_model_config_2(
            ev_data,
            household_load,
            num_ev_at_home_df,
            p_cp_rated_scaled,
            num_cp
        )
    elif config == 'config_3':
        pass

    return simulated_data


simulate_uncoordinated_model(2.4, 'config_2', 2)


def process_model_results(model: list, p_cp_rated: float):
    household_load = params.household_load
    p_cp_rated_scaled = p_cp_rated / params.charging_power_resolution_factor

    all_results = {
        'p_grid': {},
        'p_cp_rated': p_cp_rated_scaled,
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








