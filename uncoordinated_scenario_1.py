import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import params
import datetime

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=params.num_of_ev)
random_SOC_init = np.random.random(size=params.num_of_ev)


class ElectricVehicle:
    def __init__(self):
        self.capacity_of_ev: int  # (kWh)
        self.soc_init: float  # (%)
        self.at_home_status: pd.DataFrame  # (dataframe containing timestamps and binaries)
        self.soc: pd.DataFrame  # (dataframe containing timestamps and zeros initially)
        self.charging_power: pd.DataFrame  # (dataframe containing timestamps and zeros initially)

        self.t_arr: list  # a set of times of arrival
        self.soc_t_arr: dict  # key: time of arrival, value: soc

        self.soc_min = params.min_SOC  # (%)
        self.soc_max = params.max_SOC  # (%)
        self.P_EV_max = params.P_EV_max  # (kW per 15 minutes)


load_profile = pd.read_csv(filepath_or_buffer='load_profile_2_days.csv', parse_dates=True, index_col=0)
ev_profile = pd.read_csv(filepath_or_buffer='ev_profile_2_days.csv', parse_dates=True, index_col=0)

EV = [ElectricVehicle() for i in range(params.num_of_ev)]

for i in range(params.num_of_ev):
    EV[i].capacity_of_ev = max_capacity_of_EVs[i]

for i in range(params.num_of_ev):
    EV[i].soc_init = random_SOC_init[i] * EV[i].capacity_of_ev

for i in range(params.num_of_ev):
    EV[i].at_home_status = ev_profile[f'EV_{i + 1}']

for i in range(params.num_of_ev):
    EV[i].soc = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date,
                                                         periods=params.periods_in_a_day * params.num_of_days,
                                                         freq='15min'),
                              'soc': np.zeros(params.periods_in_a_day * params.num_of_days)})
    EV[i].soc.set_index('timestamp', inplace=True)

for i in range(params.num_of_ev):
    EV[i].charging_power = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date,
                                                                    periods=params.periods_in_a_day * params.num_of_days,
                                                                    freq='15min'),
                                         'charging_power': np.zeros(params.periods_in_a_day * params.num_of_days)})
    EV[i].charging_power.set_index('timestamp', inplace=True)

for i in range(params.num_of_ev):
    EV[i].soc_max = params.max_SOC * EV[i].capacity_of_ev

for i in range(params.num_of_ev):
    EV[i].soc_min = params.min_SOC * EV[i].capacity_of_ev


EV[0].t_arr = ['2019-01-01 18:00:00', '2019-01-02 18:30:00']

EV[0].soc_t_arr = {'2019-01-01 18:00:00': 0.1 * float(EV[0].capacity_of_ev),
                   '2019-01-02 18:30:00': 0.12 * float(EV[0].capacity_of_ev)}

EV[1].t_arr = ['2019-01-01 16:00:00', '2019-01-02 18:15:00']

EV[1].soc_t_arr = {'2019-01-01 16:00:00': 0.25 * float(EV[1].capacity_of_ev),
                   '2019-01-02 18:15:00': 0.2 * float(EV[1].capacity_of_ev)}


# print(EV[1].soc_t_arr['2019-01-01 16:00:00'])

# '2019-01-01 00:00:00'

merged_df = load_profile.join(ev_profile)
merged_df['n_conn_ev'] = merged_df[['EV_1', 'EV_2']].sum(axis=1).astype(int)
# print(merged_df)

for i in range(params.num_of_ev):
    for t in merged_df.index:
        # check how much power left after being used for load
        if params.P_grid_max >= merged_df['load'].loc[t]:
            cp_capacity = params.P_grid_max - merged_df['load'].loc[t]
        else:
            grid_overload = ValueError('Demand is higher than the maximum grid capacity.')
            raise grid_overload

        # check maximum charging power based on how many evs are connected
        if merged_df['n_conn_ev'].loc[t] > 0:
            max_cp_capacity = cp_capacity / merged_df['n_conn_ev'].loc[t]
        else:
            max_cp_capacity = cp_capacity

        # check if ev is at home or not
        if merged_df[f'EV_{i+1}'].loc[t] == 0:
            EV[i].charging_power.loc[t] = 0
        else:
            if max_cp_capacity >= EV[i].P_EV_max:
                EV[i].charging_power.loc[t] = EV[i].P_EV_max
            else:
                EV[i].charging_power.loc[t] = max_cp_capacity

        # tracking the SOC
        if str(t) == params.start_date:
            EV[i].soc.loc[t] = EV[i].soc_init
            EV[i].charging_power.loc[t] = 0

        elif (str(t) != params.start_date) & (str(t) not in EV[i].t_arr):
            EV[i].soc.loc[t] = (EV[i].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                EV[i].charging_power.loc[t].values)

            # make sure soc does not exceed the soc max limit
            if EV[i].soc.loc[t].values < EV[i].soc_max:
                continue
            else:
                EV[i].charging_power.loc[t] = 0
                EV[i].soc.loc[t] = EV[i].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)]

        elif (str(t) != params.start_date) & (str(t) in EV[i].t_arr):
            EV[i].soc.loc[t] = (EV[i].soc.loc[t - pd.Timedelta(minutes=params.time_resolution)] +
                                EV[i].charging_power.loc[t].values) - EV[i].soc_t_arr[str(t)]


    # print(f'\nEV_{i + 1}\n')
    # print('-------------------------------------------\n')
    # print(EV[i].soc[50:100])
    # print(EV[i].soc[100:150])
    # print(EV[i].soc[150:200])
    # print('\n-------------------------------------------\n')

# print(EV[0].soc[50:100])
# print(EV[0].soc[100:150])
# print(EV[0].soc[150:200])
#
# print(EV[1].soc[50:100])
# print(EV[1].soc[100:150])
# print(EV[1].soc[150:200])

for i in range(params.num_of_ev):
    soc_and_power = pd.concat([EV[i].soc, EV[i].charging_power], axis=1)

    print(f'\nEV_{i + 1}\n')
    print('-------------------------------------------\n')
    print(soc_and_power[:50])
    print(soc_and_power[50:100])
    print(soc_and_power[100:150])
    print(soc_and_power[150:200])
    print('-------------------------------------------\n')