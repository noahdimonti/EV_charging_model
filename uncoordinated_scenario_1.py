import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import params
import datetime

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=params.num_of_ev)
random_SOC_init = np.random.random(size=params.num_of_ev)


class ElectricVehicle():
    capacity_of_ev: int  # (kWh)
    soc_init: float  # (%)
    soc: None  # (dataframe)
    at_home_status: None  # (dataframe)
    charging_power: None  # (dataframe)

    soc_min = params.min_SOC  # (%)
    soc_max = params.max_SOC  # (%)
    P_EV_max = params.P_EV_max


EV = [ElectricVehicle() for i in range(params.num_of_ev)]

for i in range(params.num_of_ev):
    EV[i].capacity_of_ev = max_capacity_of_EVs[i]

for i in range(params.num_of_ev):
    EV[i].soc_init = random_SOC_init[i] * EV[i].capacity_of_ev

load_profile = pd.read_csv(filepath_or_buffer='load_profile_2_days.csv', parse_dates=True, index_col=0)
ev_profile = pd.read_csv(filepath_or_buffer='ev_profile_2_days.csv', parse_dates=True, index_col=0)

for i in range(params.num_of_ev):
    EV[i].at_home_status = ev_profile[f'EV_{i + 1}']

for i in range(params.num_of_ev):
    EV[i].soc = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date, periods=96 * 2, freq='15min'),
                               'soc': np.zeros(96 * 2)})
    EV[i].soc.set_index('timestamp', inplace=True)

for i in range(params.num_of_ev):
    EV[i].charging_power = pd.DataFrame({'timestamp': pd.date_range(start=params.start_date, periods=96 * 2,
                                                                    freq='15min'), 'charging_power': np.zeros(96 * 2)})
    EV[i].charging_power.set_index('timestamp', inplace=True)

# print(EV[0].charging_power.loc['2019-01-01 00:00:00'])

merged_df = load_profile.join(ev_profile)
merged_df['n_conn_ev'] = merged_df[['EV_1', 'EV_2']].sum(axis=1).astype(int)
# print(merged_df)


for t in merged_df.index:
    # print(timestep)
    # check how much power left after being taken by load
    if params.P_grid_max >= merged_df['load'].loc[t]:
        cp_capacity = params.P_grid_max - merged_df['load'].loc[t]
    else:
        grid_overload = ValueError('Demand is higher than maximum grid capacity.')
        raise grid_overload

    # check maximum charging power based on how many evs are connected
    if merged_df['n_conn_ev'].loc[t] > 0:
        max_EV_charging_power = cp_capacity / merged_df['n_conn_ev'].loc[t]
    else:
        max_EV_charging_power = cp_capacity

    # check if ev is at home or not
    if merged_df['EV_1'].loc[t] == 0:
        EV[0].charging_power.loc[t] = 0
    else:
        if max_EV_charging_power >= EV[0].P_EV_max:
            EV[0].charging_power.loc[t] = EV[0].P_EV_max
        else:
            EV[0].charging_power.loc[t] = max_EV_charging_power

    # tracking the SOC
    if str(t) == params.start_date:
        EV[0].soc.loc[t] = EV[0].soc_init
        print(t, EV[0].soc.loc[t])
    else:
        EV[0].soc.loc[t] = EV[0].soc.loc[t - pd.Timedelta(minutes=15)] + EV[0].charging_power.loc[t].values
        print(t, EV[0].soc.loc[t])

# print(EVs[0].soc.loc['2019-01-01 00:00:00'])
