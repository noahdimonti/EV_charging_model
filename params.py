import pandas as pd
import numpy as np
import pickle
from pprint import pprint

num_of_evs = 50
num_of_households = 100
'''
date options:
'2019-01-01 00:00:00'
'2022-02-21 00:00:00'
'''
start_date_time = pd.Timestamp('2022-02-21 00:00:00')
num_of_days = 7
time_resolution = 15  # minutes
periods_in_a_day = int((60 / time_resolution) * 24)

P_grid_max = 500  # (kW)
min_SOC = 0.3  # (%)
max_SOC = 0.9  # (%)
final_SOC = 0.5  # (%)
P_EV_resolution_factor = int(60 / time_resolution)
P_EV_max_list = [i / P_EV_resolution_factor for i in (1.3, 2.4, 3.7, 7.2)]
P_EV_max = P_EV_max_list[1]  # (kW per time resolution)

# EV travel distance and travel energy consumption
avg_travel_distance = 40  # (km)
travel_dist_std_dev = 5  # (km)
energy_consumption_per_km = 0.2  # (kWh/km)

# cost parameters
grid_operational_cost = 0.1  # ($/kW)

# create tariff data
'''
source: https://ieeexplore.ieee.org/abstract/document/9733283
ToU Tariff

Peak 17-21pm
Summer: 1.25
Winter: 0.36

Off peak 10am-15pm
0.08

Shoulder 6-10am, 15-17pm, 21pm-1am
0.2

Second shoulder 1-6am
0.12

Supply charge
1.1 daily

---

Flat tariff
0.378

Supply charge
0.86 daily
'''

# tariff in ($/kW)
flat_tariff_rate = 0.378
flat_tariff = pd.DataFrame({'timestamp': pd.date_range(start=start_date_time,
                                                       periods=periods_in_a_day * num_of_days,
                                                       freq=f'{time_resolution}min'),
                            'tariff': [flat_tariff_rate for i in range(periods_in_a_day * num_of_days)]})
flat_tariff.set_index('timestamp', inplace=True)

tou_tariff = pd.DataFrame({'timestamp': pd.date_range(start=start_date_time,
                                                      periods=periods_in_a_day * num_of_days,
                                                      freq=f'{time_resolution}min'),
                           'tariff': np.zeros(periods_in_a_day * num_of_days)})
tou_tariff.set_index('timestamp', inplace=True)

for t in tou_tariff.index:
    if 1 <= t.hour < 6:  # second shoulder
        tou_tariff.loc[t, 'tariff'] = 0.12
    elif 6 <= t.hour < 10:  # shoulder
        tou_tariff.loc[t, 'tariff'] = 0.2
    elif 10 <= t.hour < 15:  # off peak
        tou_tariff.loc[t, 'tariff'] = 0.08
    elif 15 <= t.hour < 17:  # shoulder
        tou_tariff.loc[t, 'tariff'] = 0.2
    elif 17 <= t.hour < 21:  # peak
        tou_tariff.loc[t, 'tariff'] = 1.25
    elif 21 <= t.hour <= 23:  # shoulder
        tou_tariff.loc[t, 'tariff'] = 0.2
    elif t.hour == 0:  # shoulder
        tou_tariff.loc[t, 'tariff'] = 0.2


def set_tariff(tariff):
    if tariff == 'flat':
        return flat_tariff
    elif tariff == 'tou':
        return tou_tariff
    elif tariff != 'flat_tariff' & tariff != 'tou_tariff':
        raise ValueError("Invalid tariff_type. Use 'flat' or 'tou'.")


tariff_type = 'flat'
tariff = set_tariff(tariff_type)

# execute EV data cleaning
exec(open('vista_data_cleaning.py').read())


# create EV class
class ElectricVehicle:
    def __init__(self):
        self.at_home_status = pd.DataFrame  # (dataframe containing timestamps and binaries)
        self.soc = pd.DataFrame  # (dataframe containing timestamps and zeros initially)
        self.charging_power = pd.DataFrame  # (dataframe containing timestamps and zeros initially)
        self.t_dep = []  # a set of times of departure
        self.t_arr = []  # a set of times of arrival
        self.travel_energy = []  # a set of values for energy consumption, aligning with t_dep and t_arr
        self.travel_energy_t_arr = {}  # a dict that stores travel_energy associated with t_arr
        # (keys: t_arr, Values: travel_energy)

        self.capacity_of_ev = None  # (kWh)
        self.soc_init = None  # (kWh)
        self.soc_final = None  # (kWh)

        self.soc_min = min_SOC  # (kWh)
        self.soc_max = max_SOC  # (kWh)
        self.P_EV_max = P_EV_max  # (kW per 15 minutes)

        self.soc = pd.DataFrame({'timestamp': pd.date_range(start=start_date_time,
                                                            periods=periods_in_a_day * num_of_days,
                                                            freq=f'{time_resolution}min'),
                                 'soc': np.zeros(periods_in_a_day * num_of_days)})
        self.soc.set_index('timestamp', inplace=True)

        self.charging_power = pd.DataFrame({'timestamp': pd.date_range(start=start_date_time,
                                                                       periods=periods_in_a_day * num_of_days,
                                                                       freq=f'{time_resolution}min'),
                                            'charging_power': np.zeros(periods_in_a_day * num_of_days)})
        self.charging_power.set_index('timestamp', inplace=True)


# open data
with open('ev_data.pkl', 'rb') as f:
    ev_data = pickle.load(f)

# instantiate EV objects in a list
EV = [ElectricVehicle() for i in range(num_of_evs)]

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=num_of_evs)
random_SOC_init = np.random.uniform(low=min_SOC, high=max_SOC, size=num_of_evs)

ev_at_home_status_profile_list = []
ev_charging_power_list = []

# take data from pickle file and put them in EV class attributes
for ev_id in range(num_of_evs):
    # initialise ev parameters
    EV[ev_id].at_home_status = ev_data[ev_id].at_home_status
    EV[ev_id].t_arr = ev_data[ev_id].t_arr
    EV[ev_id].t_dep = ev_data[ev_id].t_dep
    EV[ev_id].travel_energy = ev_data[ev_id].travel_energy

    EV[ev_id].capacity_of_ev = max_capacity_of_EVs[ev_id]
    EV[ev_id].soc_init = random_SOC_init[ev_id] * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_max = max_SOC * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_min = min_SOC * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_final = final_SOC * EV[ev_id].capacity_of_ev

    # create a list of ev at home status dataframes
    ev_at_home_status_profile_list.append(EV[ev_id].at_home_status)

    # create a list of ev charging power dataframes
    ev_charging_power_list.append(EV[ev_id].charging_power)

    np.random.seed(ev_id)
    # set travel_energy_consumption
    if len(EV[ev_id].t_dep) == len(EV[ev_id].t_arr):
        for idx, t in enumerate(EV[ev_id].t_arr):
            rand_distance = np.random.normal(loc=avg_travel_distance, scale=travel_dist_std_dev, size=1)
            rand_travel_consumption = energy_consumption_per_km * rand_distance  # in kWh

            EV[ev_id].travel_energy.append(rand_travel_consumption)

            EV[ev_id].travel_energy_t_arr[t] = rand_travel_consumption
