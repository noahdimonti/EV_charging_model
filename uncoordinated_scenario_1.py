import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from pprint import pprint
import params
import pickle

exec(open('vista_data_cleaning.py').read())


class ElectricVehicle:
    def __init__(self):
        self.at_home_status = pd.DataFrame  # (dataframe containing timestamps and binaries)
        self.soc = pd.DataFrame  # (dataframe containing timestamps and zeros initially)
        self.charging_power = pd.DataFrame  # (dataframe containing timestamps and zeros initially)
        self.t_arr = []  # a set of times of arrival
        self.soc_t_arr = {}  # key: time of arrival, value: soc

        self.capacity_of_ev = None  # (kWh)
        self.soc_init = None  # (%)

        self.soc_min = params.min_SOC  # (%)
        self.soc_max = params.max_SOC  # (%)
        self.P_EV_max = params.P_EV_max  # (kW per 15 minutes)

        self.soc = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date_time,
                                                            periods=params.periods_in_a_day * params.num_of_days,
                                                            freq='15min'),
                                 'soc': np.zeros(params.periods_in_a_day * params.num_of_days)})
        self.soc.set_index('timestamp', inplace=True)

        self.charging_power = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date_time,
                                                                       periods=params.periods_in_a_day * params.num_of_days,
                                                                       freq='15min'),
                                            'charging_power': np.zeros(params.periods_in_a_day * params.num_of_days)})
        self.charging_power.set_index('timestamp', inplace=True)


with open('ev_data.pkl', 'rb') as f:
    ev_data = pickle.load(f)

EV = [ElectricVehicle() for i in range(params.num_of_evs)]

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=params.num_of_evs)
random_SOC_init = np.random.random(size=params.num_of_evs)

ev_at_home_status_profile_list = []
ev_charging_power_list = []

for ev_id in range(params.num_of_evs):
    # initialise ev parameters
    EV[ev_id].at_home_status = ev_data[ev_id].at_home_status
    EV[ev_id].t_arr = ev_data[ev_id].t_arr

    EV[ev_id].capacity_of_ev = max_capacity_of_EVs[ev_id]
    EV[ev_id].soc_init = random_SOC_init[ev_id] * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_max = params.max_SOC * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_min = params.min_SOC * EV[ev_id].capacity_of_ev

    # create a list of ev at home status dataframes
    ev_at_home_status_profile_list.append(EV[ev_id].at_home_status)

    # create a list of ev charging power dataframes
    ev_charging_power_list.append(EV[ev_id].charging_power)

    # set soc_t_arr
    for idx, t in enumerate(EV[ev_id].t_arr):
        np.random.seed(idx)
        random_percentage = np.random.uniform(low=0.05, high=0.25)
        EV[ev_id].soc_t_arr[t] = random_percentage * float(EV[ev_id].capacity_of_ev)

household_load = pd.read_csv(filepath_or_buffer='load_profile_7_days_85_households.csv', parse_dates=True, index_col=0)
# print(load_profile)
all_ev_profiles = pd.concat(ev_at_home_status_profile_list, axis=1)
all_ev_profiles['n_connected_ev'] = all_ev_profiles.sum(axis=1).astype(int)
# print(all_ev_profiles['n_connected_ev'])

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
            EV[ev_id].charging_power.loc[t] = 0
        else:
            # assign ev charging power when ev is at home
            if max_cp_capacity.values >= EV[ev_id].P_EV_max:
                EV[ev_id].charging_power.loc[t] = EV[ev_id].P_EV_max
            elif max_cp_capacity.values < EV[ev_id].P_EV_max:
                EV[ev_id].charging_power.loc[t] = max_cp_capacity.values

        # tracking the SOC
        if t == params.start_date_time:
            EV[ev_id].soc.loc[t] = EV[ev_id].soc_init
            EV[ev_id].charging_power.loc[t] = 0

        elif (t != params.start_date_time) & (t not in EV[ev_id].t_arr):
            EV[ev_id].soc.loc[t] = (EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                    EV[ev_id].charging_power.loc[t].values)

            # make sure soc does not exceed the soc max limit
            if EV[ev_id].soc.loc[t].values <= EV[ev_id].soc_max:
                pass
            else:
                # calculate how much power needed to charge until soc reaches soc_max
                remaining_to_charge = (EV[ev_id].soc_max -
                                       EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)].values)

                EV[ev_id].soc.loc[t] = (EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                        remaining_to_charge)

                EV[ev_id].charging_power.loc[t] = remaining_to_charge

        elif (t != params.start_date_time) & (t in EV[ev_id].t_arr):
            EV[ev_id].soc.loc[t] = (EV[ev_id].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                    EV[ev_id].charging_power.loc[t].values) - EV[ev_id].soc_t_arr[t]

# for ev_id in range(params.num_of_evs):
#     soc_and_power = pd.concat(objs=[EV[ev_id].at_home_status, EV[ev_id].soc, EV[ev_id].charging_power], axis=1)

# print(f'\nEV_{ev_id + 1}\n')
# print('-------------------------------------------\n')
# print(soc_and_power[:50])
# print(soc_and_power[50:100])
# print(soc_and_power[100:150])
# print(soc_and_power[150:200])
# print('-------------------------------------------\n')

ev_power_profile = pd.concat(ev_charging_power_list, axis=1)
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

fig = go.Figure()

fig.add_trace(go.Scatter(x=load_profile.index, y=load_profile['household_load'], name='household_load'))
fig.add_trace(go.Scatter(x=load_profile.index, y=load_profile['total_load'], name='total_load'))
fig.update_layout(title='Load Profile (85 Households and 50 EVs)',
                  xaxis_title='Timestamp',
                  yaxis_title='Load (kW)')
fig.show()
