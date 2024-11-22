import pandas as pd
import numpy as np
from pprint import pprint
import params
import create_ev_data
import os

P_EV_max = 2.4 / params.P_EV_resolution_factor


def create_model_instance(tariff_type: str, num_of_evs: int, avg_travel_distance: float, min_soc: float):
    # instantiate EV objects
    ev_data = create_ev_data.main(num_of_evs, avg_travel_distance, min_soc)

    # create ev at home pattern profile
    all_ev_profiles = pd.concat([ev.at_home_status for ev in ev_data], axis=1)
    all_ev_profiles['n_ev_at_home'] = all_ev_profiles.sum(axis=1).astype(int)

    # create load profile
    household_load = params.household_load

    # uncoordinated charging scenario algorithm
    for ev_id in range(num_of_evs):
        for t in all_ev_profiles.index:
            # check how much power left after being used for load
            if params.P_grid_max >= household_load.loc[t].values:
                ccp_capacity = params.P_grid_max - household_load.loc[t]
            else:
                grid_overload = ValueError('Demand is higher than the maximum grid capacity.')
                raise grid_overload

            # check maximum charging power based on how many evs are connected
            if all_ev_profiles['n_ev_at_home'].loc[t] > 0:
                max_cp_capacity = ccp_capacity / all_ev_profiles['n_ev_at_home'].loc[t]
            else:
                max_cp_capacity = ccp_capacity

            # check if ev is at home or not
            if all_ev_profiles[f'EV_ID{ev_id}'].loc[t] == 0:
                ev_data[ev_id].charging_power.loc[t] = 0
            else:
                # assign ev charging power when ev is at home
                if max_cp_capacity.values >= P_EV_max:
                    ev_data[ev_id].charging_power.loc[t] = P_EV_max
                elif max_cp_capacity.values < P_EV_max:
                    ev_data[ev_id].charging_power.loc[t] = max_cp_capacity.values

            # tracking the SOC
            time_delta = pd.Timedelta(minutes=params.time_resolution)

            if t == params.start_date_time:
                ev_data[ev_id].soc.loc[t] = ev_data[ev_id].soc_init
                ev_data[ev_id].charging_power.loc[t] = 0

            elif (t != params.start_date_time) & (t not in ev_data[ev_id].t_arr):
                ev_data[ev_id].soc.loc[t] = (ev_data[ev_id].soc.loc[t - time_delta] +
                                               ev_data[ev_id].charging_power.loc[t].values)

                # make sure soc does not exceed the soc max limit
                if ev_data[ev_id].soc.loc[t].values <= ev_data[ev_id].soc_max:
                    pass
                else:
                    # calculate how much power needed to charge until soc reaches soc_max
                    remaining_to_charge = (ev_data[ev_id].soc_max - ev_data[ev_id].soc.loc[t - time_delta].values)

                    ev_data[ev_id].soc.loc[t] = (ev_data[ev_id].soc.loc[t - time_delta] + remaining_to_charge)

                    ev_data[ev_id].charging_power.loc[t] = remaining_to_charge

            elif (t != params.start_date_time) & (t in ev_data[ev_id].t_arr):
                ev_data[ev_id].soc.loc[t] = ((ev_data[ev_id].soc.loc[t - time_delta] +
                                               ev_data[ev_id].charging_power.loc[t].values) -
                                               ev_data[ev_id].travel_energy_t_arr[t])


    # results data collection
    ev_power_profile = pd.concat([ev.charging_power for ev in ev_data], axis=1)
    ev_power_profile['ev_load'] = ev_power_profile.sum(axis=1)
    print(ev_power_profile.head(20))

    df = pd.concat(objs=[household_load, ev_power_profile['ev_load']], axis=1)
    df['total_load'] = df.sum(axis=1)
    print(df)

    max_household_load = df['household_load'].max()
    max_load = df['total_load'].max()

    print(f'P_EV_max: {P_EV_max}')
    print(f'max_household_load: {max_household_load}')
    print(f'max_total_load: {max_load}')
    print(df.loc[df['total_load'] > params.P_grid_max])


create_model_instance('flat', 5, 40, 0.3)