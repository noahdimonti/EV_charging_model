import pyomo as pyo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pprint import pprint
import params

np.random.seed(0)
max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=params.num_of_ev)
random_SOC_init = np.random.random(size=params.num_of_ev)

load_profile = pd.read_csv(filepath_or_buffer='load_profile.csv', parse_dates=True, index_col=0)
ev_profile = pd.read_csv(filepath_or_buffer='ev_profile_2_days.csv', parse_dates=True, index_col=0)
ev_profile = ev_profile.rename(columns={'EV_ID4072': 'EV_1', 'EV_ID7090': 'EV_2'})
