import pandas as pd

num_of_evs = 80  # (units)
time_resolution = 15  # minutes
start_date_time = pd.Timestamp('2022-02-21 00:00:00')
periods_in_a_day = int((60 / time_resolution) * 24)
num_of_days = 7
P_grid_max = 150  # (kW)
min_SOC = 0.2  # (%)
max_SOC = 0.9  # (%)
P_EV_max = 2.4 / int(60 / time_resolution)  # (kW per time resolution)
