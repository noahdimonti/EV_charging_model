import pandas as pd
import numpy as np
from pprint import pprint
import params
import create_ev_data
import os
from classes.UncoordinatedModel import UncoordinatedModel
import output_collection

p_ev_max = 2.4


def create_model_instance(tariff_type: str, num_of_evs: int, avg_travel_distance: float,
                          min_soc: float):
    # instantiate EV objects
    ev_data = create_ev_data.main(num_of_evs, avg_travel_distance, min_soc)

    # create ev at home pattern profile
    all_ev_profiles = pd.concat([ev.at_home_status for ev in ev_data], axis=1)
    all_ev_profiles['n_ev_at_home'] = all_ev_profiles.sum(axis=1).astype(int)

    # create household load profile
    household_load = params.household_load

    # convert p_ev_max according to resolution
    p_ev_max_per_resolution = p_ev_max / params.P_EV_resolution_factor

    # uncoordinated charging scenario algorithm
    for id, ev in enumerate(ev_data):
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
            if all_ev_profiles[f'EV_ID{id}'].loc[t] == 0:
                ev.charging_power.loc[t] = 0
            else:
                # assign ev charging power when ev is at home
                if max_cp_capacity.values >= p_ev_max_per_resolution:
                    # if available charging power is higher than p_ev_max, charging power is assigned as p_ev_max
                    ev.charging_power.loc[t] = p_ev_max_per_resolution
                elif max_cp_capacity.values < p_ev_max_per_resolution:
                    # if available charging power is less, then assign whatever is available
                    ev.charging_power.loc[t] = max_cp_capacity.values

            # tracking the SOC
            time_delta = pd.Timedelta(minutes=params.time_resolution)

            if t == params.start_date_time:
                ev.soc.loc[t] = ev.soc_init
                ev.charging_power.loc[t] = 0

            elif (t != params.start_date_time) & (t not in ev.t_arr):
                ev.soc.loc[t] = (ev.soc.loc[t - time_delta] +
                                 ev.charging_power.loc[t].values)

                # make sure soc does not exceed the soc max limit
                if ev.soc.loc[t].values <= ev.soc_max:
                    pass
                else:
                    # calculate how much power needed to charge until soc reaches soc_max
                    remaining_to_charge = (ev.soc_max - ev.soc.loc[t - time_delta].values)

                    ev.soc.loc[t] = (ev.soc.loc[t - time_delta] + remaining_to_charge)

                    ev.charging_power.loc[t] = remaining_to_charge

            elif (t != params.start_date_time) & (t in ev.t_arr):
                ev.soc.loc[t] = ((ev.soc.loc[t - time_delta] + ev.charging_power.loc[t].values) -
                                 ev.travel_energy_t_arr[t])

    # instantiate model
    model = UncoordinatedModel(f'US1_{tariff_type}_{num_of_evs}EVs_{avg_travel_distance}km_SOCmin{int(min_soc * 100)}%')

    # assign values to model attributes
    df = pd.concat([ev.charging_power for ev in ev_data], axis=1)
    df['ev_load'] = df.sum(axis=1)
    df['household_load'] = params.household_load
    df['grid'] = df['ev_load'] + df['household_load']
    df['total_load'] = df['ev_load'] + df['household_load']

    model.ev_load = df['ev_load']
    model.household_load = df['household_load']
    model.grid = df['grid']
    model.total_load = df['total_load']

    model.p_ev_max = p_ev_max
    model.num_of_cps = num_of_evs

    return model


tariff = 'flat'
num_of_evs = 10
avg_travel_distance = 30
min_soc = 0.3

# ev = create_model_instance(tariff, num_of_evs, avg_travel_distance, min_soc)
# output = output_collection.collect_model_outputs(ev, 'uncoordinated', tariff, num_of_evs, avg_travel_distance, min_soc)
# pprint(output.to_dict())
