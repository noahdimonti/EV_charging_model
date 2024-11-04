import pyomo as pyo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint

num_of_ev = 2  # (units)
P_grid_max = 500  # (kW)
min_SOC = 0.2  # (%)
max_SOC = 0.9  # (%)
P_EV_max = [2.4, 3.7, 7.4]  # (kW)

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=num_of_ev)
random_SOC_init = np.random.random(size=num_of_ev)


class ElectricVehicle():
    capacity_of_ev: int  # (kWh)
    soc_init: float  # (%)

    soc_min = min_SOC  # (%)
    soc_max = max_SOC  # (%)


EVs = [ElectricVehicle() for i in range(num_of_ev)]

for i in range(num_of_ev):
    EVs[i].capacity_of_ev = max_capacity_of_EVs[i]

for i in range(num_of_ev):
    EVs[i].soc_init = random_SOC_init[i]

print(EVs[0].soc_max)

load_profile = pd.read_csv(filepath_or_buffer='load_profile.csv', parse_dates=True, index_col=0)
ev_profile = pd.read_csv(filepath_or_buffer='ev_profile.csv', parse_dates=True, index_col=0)
ev_profile = ev_profile.rename(columns={'EV_ID4072': 'EV_1', 'EV_ID7090': 'EV_2'})

