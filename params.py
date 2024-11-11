import pandas as pd
import numpy as np
import pickle

num_of_evs = 1  # (units)
time_resolution = 15  # minutes
start_date_time = pd.Timestamp('2022-02-21 00:00:00')
periods_in_a_day = int((60 / time_resolution) * 24)
num_of_days = 7
P_grid_max = 250  # (kW)
min_SOC = 0.2  # (%)
max_SOC = 0.9  # (%)
P_EV_max = 2.4 / int(60 / time_resolution)  # (kW per time resolution)
energy_cost = 0.1  # ($/kW)


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

        self.soc_min = min_SOC  # (%)
        self.soc_max = max_SOC  # (%)
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


with open('ev_data.pkl', 'rb') as f:
    ev_data = pickle.load(f)

EV = [ElectricVehicle() for i in range(num_of_evs)]

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=num_of_evs)
random_SOC_init = np.random.random(size=num_of_evs)

ev_at_home_status_profile_list = []
ev_charging_power_list = []

for ev_id in range(num_of_evs):
    # initialise ev parameters
    EV[ev_id].at_home_status = ev_data[ev_id].at_home_status
    EV[ev_id].t_arr = ev_data[ev_id].t_arr

    EV[ev_id].capacity_of_ev = max_capacity_of_EVs[ev_id]
    EV[ev_id].soc_init = random_SOC_init[ev_id] * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_max = max_SOC * EV[ev_id].capacity_of_ev
    EV[ev_id].soc_min = min_SOC * EV[ev_id].capacity_of_ev

    # create a list of ev at home status dataframes
    ev_at_home_status_profile_list.append(EV[ev_id].at_home_status)

    # create a list of ev charging power dataframes
    ev_charging_power_list.append(EV[ev_id].charging_power)

    # set soc_t_arr
    for idx, t in enumerate(EV[ev_id].t_arr):
        np.random.seed(idx)
        random_percentage = np.random.uniform(low=0.05, high=0.25)
        EV[ev_id].soc_t_arr[t] = random_percentage * float(EV[ev_id].capacity_of_ev)
