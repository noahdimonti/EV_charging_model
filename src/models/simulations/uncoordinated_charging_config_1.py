import pandas as pd
from src.config import params, ev_params, independent_variables
from pprint import pprint


def main(p_cp_rated: float):
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
    for ev_id, ev in enumerate(ev_data):
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
                        soc_ev[-1] -= ev.travel_energy[ev_id]

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

        ev.charging_power['charging_power'] = p_ev
        ev.soc['soc'] = soc_ev
        print(ev.charging_power)
        print(ev.soc)
        pprint(ev.__dict__)

        break


main(2.4)
