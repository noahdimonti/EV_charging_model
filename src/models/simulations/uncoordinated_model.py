import pandas as pd
from typing import Optional, Dict
from src.config import params, ev_params
from src.models.simulations import config_1, config_2, config_3
from src.data_processing.electric_vehicle import ElectricVehicle


def simulate_uncoordinated_model(
        p_cp_rated: float,
        config: str,
        config_attribute: int | dict) -> list[ElectricVehicle]:
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

    if config == 'config_1':
        config_1_simulator = config_1.UncoordinatedModelConfig1(
            ev_data,
            household_load,
            num_ev_at_home_df,
            p_cp_rated_scaled
        )
        return config_1_simulator.run()

    elif config == 'config_2':
        if type(config_attribute) == int:
            config_2_simulator = config_2.UncoordinatedModelConfig2(
                ev_data,
                household_load,
                p_cp_rated_scaled,
                config_attribute
            )
            return config_2_simulator.run()

        else:
            raise ValueError('Provide number of CP for configuration 2 simulation.')

    elif config == 'config_3':
        if type(config_attribute) == dict:
            config_3_simulator = config_3.UncoordinatedModelConfig3(
                ev_data,
                household_load,
                p_cp_rated_scaled,
                config_attribute
            )
            return config_3_simulator.run()

        else:
            raise ValueError('Provide a dictionary of EV to CP assignment for configuration 3 simulation.')


assignment = {
    0: [0, 4, 5, 7, 9],
    2: [1, 2, 3, 6, 8]
}
data = simulate_uncoordinated_model(2.4, 'config_3', config_attribute=assignment)
print(data)


def process_model_results(model: list[ElectricVehicle], p_cp_rated: float) -> dict[str, float | dict]:
    household_load = params.household_load
    p_cp_rated_scaled = p_cp_rated / params.charging_power_resolution_factor

    all_results = {
        'p_grid': {},
        'p_cp_rated': p_cp_rated_scaled,
        'num_cp': None,
        'p_ev': {},
        'soc_ev': {},
    }

    for i, ev in enumerate(model):
        for t in params.timestamps:
            # Extract p_grid
            all_results['p_grid'][t] = household_load.loc[t].values.item() + sum(e.charging_power.loc[t].values.item() for e in model)

            # Number of CP
            all_results['num_cp'] = ...

            # Extract charging power
            all_results['p_ev'][(i, t)] = ev.charging_power.loc[t].values.item()

            # Extract SOC
            all_results['soc_ev'][(i, t)] = ev.soc.loc[t].values.item()

    return all_results








