import pandas as pd
import numpy as np
from pprint import pprint


# --------------------------
# Time Settings
# --------------------------
'''
date options:
'2019-01-01 00:00:00'
'2022-02-21 00:00:00'
'''
start_date_time = pd.Timestamp('2022-02-21 00:00:00')
num_of_days = 7

time_resolution = 15  # minutes
periods_in_a_day = int((60 / time_resolution) * 24)

timestamps = pd.date_range(start=start_date_time,
                           periods=periods_in_a_day * num_of_days,
                           freq=f'{time_resolution}min')
# Define subset of set T for day d
T_d = timestamps.groupby(timestamps.date)

# Create a df with week column
tmp = pd.DataFrame({'timestamp': timestamps}).set_index('timestamp')
tmp['week'] = tmp.index.isocalendar().week

# Define subset of set D for week w
D_w = tmp.resample('D').first()
D_w = D_w.groupby('week').apply(lambda x: x.index.date.tolist()).to_dict()
length_D_w = 7

# Define a subset of T for week w
T_w = tmp.groupby('week').apply(lambda x: x.index.tolist()).to_dict()


num_of_evs = 5
num_of_households = 10


# --------------------------
# EV Charge Scheduling Settings
# --------------------------
min_num_charging_days = 1
max_num_charging_days = 4
max_charged_evs_daily_margin = 0


# --------------------------
# Charging Point Settings
# --------------------------
num_cp_min = 1
num_cp_max = num_of_evs - 1


# --------------------------
# EV SOC Settings
# --------------------------
SOC_max = 0.9  # (%)
SOC_critical = 0.1  # (%)
min_initial_soc = 0.4  # (%)
max_initial_soc = 0.6  # (%)

ev_capacity_range_low = 35  # (kWh)
ev_capacity_range_high = 60  # (kWh)

charging_efficiency = 0.95  # (%)


# --------------------------
# EV Charging Power Settings
# --------------------------
charging_power_resolution_factor = int(60 / time_resolution)
p_cp_rated_options = [1.3, 2.4, 3.7, 7.2]
p_cp_rated_options_scaled = [
    i / charging_power_resolution_factor for i in p_cp_rated_options  # values: [0.325, 0.6, 0.925, 1.8]
]
p_cp_rated_min = min(p_cp_rated_options_scaled)
p_cp_rated_max = max(p_cp_rated_options_scaled)


# --------------------------
# EV Travel Settings
# --------------------------
avg_travel_distance = 35  # (km)
travel_dist_std_dev = 5  # (km)
energy_consumption_per_km = 0.2  # (kWh/km)
travel_freq_probability = {
    'once': 0.6,
    'twice': 0.3,
    'thrice': 0.1
}
min_time_at_home = time_resolution * 4  # EV stays at home for a minimum of x hrs


# Cost of EV charger installation
'''
Cost of EV charger installation

Wall socket (1.3kW and 2.4kW): $200
Schneider EV Link (source: https://www.solarchoice.net.au/products/ev-chargers/schneider-evlink-home/)
3.7kW: $1,350
7.2kW: $1,500

Charger maintenance cost for L1 and L2 chargers per year: $400
'''

# Tariff rates data_processing
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

# --------------------------
# Tariff Settings
# --------------------------
flat_tariff_rate = 0.378
flat_daily_supply_charge = 0.86

tou_peak_rate = 1.25
tou_shoulder_rate = 0.2
tou_second_shoulder_rate = 0.12
tou_off_peak_rate = 0.08
tou_daily_supply_charge = 1.1


# Generate flat and ToU tariff data_processing
def create_flat_tariff(timestamps):
    return pd.Series([flat_tariff_rate] * len(timestamps), index=timestamps)


def create_tou_tariff(timestamps):
    df = pd.Series([np.zeros] * len(timestamps), index=timestamps)

    for t in df.index:
        if 1 <= t.hour < 6:
            df.loc[t] = tou_second_shoulder_rate
        elif 6 <= t.hour < 10 or 15 <= t.hour < 17 or 21 <= t.hour <= 23 or t.hour == 0:
            df.loc[t] = tou_shoulder_rate
        elif 10 <= t.hour < 15:
            df.loc[t] = tou_off_peak_rate
        elif 17 <= t.hour < 21:
            df.loc[t] = tou_peak_rate

    return df


tariff_dict = {
    'flat': create_flat_tariff(timestamps),
    'tou': create_tou_tariff(timestamps)
}

daily_supply_charge_dict = {
    'flat': flat_daily_supply_charge,
    'tou': tou_daily_supply_charge
}


# --------------------------
# Power Grid Settings
# --------------------------
P_grid_max = 500  # (kW)


# --------------------------
# Household Load Settings
# --------------------------
household_load_path = f'../../data/interim/load_profile_{num_of_days}_days_{num_of_households}_households.csv'
household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)


# --------------------------
# Investment and Maintenance Costs
# --------------------------
investment_cost_list = [200, 200, 1350, 1500]  # per EV charger
investment_cost = {p_cp: investment_cost
                   for p_cp, investment_cost in zip(p_cp_rated_options_scaled, investment_cost_list)
                   }  # values: {0.325: 200, 0.6: 200, 0.925: 1350, 1.8: 1500}
annual_maintenance_cost = 400


# Define colours for printing
RESET = "\033[0m"  # Reset to default
RED = '\033[31m'  # Red color (e.g., for warning or error)
GREEN = '\033[32m'  # Green color (e.g., for success)