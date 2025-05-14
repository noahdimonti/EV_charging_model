import pandas as pd
from src.config import params, ev_params


def uncoordinated_model_config_1(
        ev_data: list,
        household_load: pd.DataFrame,
        num_ev_at_home: pd.DataFrame,
        p_cp_rated_scaled: float,
):
    # Iterate over EVs
    for i, ev in enumerate(ev_data):
        # Initialise charging power and soc empty list
        p_ev = []
        soc_ev = []

        for t in params.timestamps:
            # Calculate CCP max capacity
            ccp_capacity = params.P_grid_max - household_load.loc[t].values.item()

            # calculate maximum charging power per EV divided evenly
            available_power_at_cp = (ccp_capacity / num_ev_at_home.loc[t].values.item()) \
                if num_ev_at_home.loc[t].values > 1 else ccp_capacity

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
