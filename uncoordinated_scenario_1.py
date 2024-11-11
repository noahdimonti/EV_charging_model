import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pprint import pprint
import params
import pickle

# initiate EV parameters
exec(open('params.py').read())

# create load profile
household_load = pd.read_csv(filepath_or_buffer='load_profile_7_days_85_households.csv', parse_dates=True, index_col=0)
# print(load_profile)

# create ev at home pattern profile
all_ev_profiles = pd.concat(params.ev_at_home_status_profile_list, axis=1)
all_ev_profiles['n_connected_ev'] = all_ev_profiles.sum(axis=1).astype(int)
# print(all_ev_profiles['n_connected_ev'])

# uncoordinated charging scenario algorithm
for ev_id in range(params.num_of_evs):
    for t in all_ev_profiles.index:
        # check how much power left after being used for load
        if params.P_grid_max >= household_load.loc[t].values:
            ccp_capacity = params.P_grid_max - household_load.loc[t]
        else:
            grid_overload = ValueError('Demand is higher than the maximum grid capacity.')
            raise grid_overload

        # check maximum charging power based on how many evs are connected
        if all_ev_profiles['n_connected_ev'].loc[t] > 0:
            max_cp_capacity = ccp_capacity / all_ev_profiles['n_connected_ev'].loc[t]
        else:
            max_cp_capacity = ccp_capacity

        # check if ev is at home or not
        if all_ev_profiles[f'EV_ID{ev_id}'].loc[t] == 0:
            params.EV[ev_id].charging_power.loc[t] = 0
        else:
            # assign ev charging power when ev is at home
            if max_cp_capacity.values >= params.EV[ev_id].P_EV_max:
                params.EV[ev_id].charging_power.loc[t] = params.EV[ev_id].P_EV_max
            elif max_cp_capacity.values < params.EV[ev_id].P_EV_max:
                params.EV[ev_id].charging_power.loc[t] = max_cp_capacity.values

        # tracking the SOC
        if t == params.start_date_time:
            params.EV[ev_id].soc.loc[t] = params.EV[ev_id].soc_init
            params.EV[ev_id].charging_power.loc[t] = 0

        elif (t != params.start_date_time) & (t not in params.EV[ev_id].t_arr):
            params.EV[ev_id].soc.loc[t] = (params.EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                           params.EV[ev_id].charging_power.loc[t].values)

            # make sure soc does not exceed the soc max limit
            if params.EV[ev_id].soc.loc[t].values <= params.EV[ev_id].soc_max:
                pass
            else:
                # calculate how much power needed to charge until soc reaches soc_max
                remaining_to_charge = (params.EV[ev_id].soc_max -
                                       params.EV[ev_id].soc.loc[
                                           t - pd.Timedelta(minutes=params.time_resolution)].values)

                params.EV[ev_id].soc.loc[t] = (
                            params.EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                            remaining_to_charge)

                params.EV[ev_id].charging_power.loc[t] = remaining_to_charge

        elif (t != params.start_date_time) & (t in params.EV[ev_id].t_arr):
            params.EV[ev_id].soc.loc[t] = (params.EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                           params.EV[ev_id].charging_power.loc[t].values) - params.EV[ev_id].soc_t_arr[
                                              t]

# for ev_id in range(params.num_of_evs):
#     soc_and_power = pd.concat(objs=[EV[ev_id].at_home_status, EV[ev_id].soc, EV[ev_id].charging_power], axis=1)

# print(f'\nEV_{ev_id + 1}\n')
# print('-------------------------------------------\n')
# print(soc_and_power[:50])
# print(soc_and_power[50:100])
# print(soc_and_power[100:150])
# print(soc_and_power[150:200])
# print('-------------------------------------------\n')

ev_power_profile = pd.concat(params.ev_charging_power_list, axis=1)
ev_power_profile['ev_load'] = ev_power_profile.sum(axis=1)
# print(ev_power_profile.head(20))

load_profile = pd.concat(objs=[household_load, ev_power_profile['ev_load']], axis=1)
load_profile['total_load'] = load_profile.sum(axis=1)
print(load_profile)

max_household_load = load_profile['household_load'].max()
max_load = load_profile['total_load'].max()

print(f'max_household_load: {max_household_load}')
print(f'max_total_load: {max_load}')
print(load_profile.loc[load_profile['total_load'] > params.P_grid_max])

#%%
import plotly.graph_objects as go

peak_total = []
for day in set(load_profile.index.day):
    daily_peak = load_profile.loc[(load_profile.index.day == day), 'household_load'].max()
    peak_total.append(daily_peak)

avg_daily_peak = sum(peak_total) / len(peak_total)
print(avg_daily_peak)

# tmp = load_profile.loc[load_profile.index.day == min(load_profile.index.day)]
tmp = load_profile

fig = go.Figure()

fig.add_trace(go.Scatter(x=tmp.index, y=tmp['household_load'], name='Household load'))
fig.add_trace(go.Scatter(x=tmp.index, y=tmp['total_load'], name='Total household and EV load'))
fig.add_trace(go.Scatter(x=tmp.index, y=[params.P_grid_max for i in range(len(tmp.index))], name='Maximum grid power'))
fig.add_trace(
    go.Scatter(x=tmp.index, y=[avg_daily_peak for i in range(len(tmp.index))], name='Average daily household peak'))
fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs)',
                  xaxis_title='Timestamp',
                  yaxis_title='Load (kW)')
fig.show()
