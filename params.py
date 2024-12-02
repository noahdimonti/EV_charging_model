import pandas as pd
import numpy as np
import os

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

# --------------------------
# Power Grid Settings
# --------------------------
P_grid_max = 500  # (kW)

# --------------------------
# EV SOC Settings
# --------------------------
max_SOC = 0.9  # (%)
min_initial_soc = 0.4  # (%)
max_initial_soc = 0.7  # (%)

ev_capacity_range_low = 35  # (kWh)
ev_capacity_range_high = 60  # (kWh)

final_SOC_default = 0.5  # (%)

# --------------------------
# EV Charging Power Settings
# --------------------------
P_EV_resolution_factor = int(60 / time_resolution)
max_charging_power_options = [1.3, 2.4, 3.7, 7.2]
P_EV_max_list = [i / P_EV_resolution_factor for i in max_charging_power_options]

# --------------------------
# EV Travel Settings
# --------------------------
travel_dist_std_dev = 5  # (km)
energy_consumption_per_km = 0.2  # (kWh/km)
travel_freq_probability = {
    'once': 0.6,
    'twice': 0.3,
    'thrice': 0.1
}
ev_min_time_at_home = time_resolution * 6  # EV stays at home for a minimum of 1.5 hrs

# Cost of EV charger installation
'''
Cost of EV charger installation

Wall socket (1.3kW and 2.4kW): $200
Schneider EV Link (source: https://www.solarchoice.net.au/products/ev-chargers/schneider-evlink-home/)
3.7kW: $1,350
7.2kW: $1,500

Charger maintenance cost for L1 and L2 chargers per year: $400
'''

# Tariff rates data
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


# Generate flat and ToU tariff data
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
# Penalty Costs
# --------------------------
charging_discontinuity_penalty = 0.01
peak_penalty = 0.01

# --------------------------
# Investment and Maintenance Costs
# --------------------------
investment_cost_list = [200, 200, 1350, 1500]  # per EV charger
investment_cost = {P_EV_max: investment_cost
                   for P_EV_max, investment_cost in zip(P_EV_max_list, investment_cost_list)}
annual_maintenance_cost = 400

#  --------------------------
# Household Load Profile
# --------------------------
num_of_households = 100


# Get the absolute path of the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

# Define the input data directory and file path relative to the project root
household_load_dir = os.path.join(project_root, 'input_data')
household_load_file = f'load_profile_{num_of_days}_days_{num_of_households}_households.csv'
household_load_path = os.path.join(household_load_dir, household_load_file)

try:
    household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)
except FileNotFoundError:
    print(f'Warning: Household load file not found at {household_load_path}.')


# Define colours for printing
RESET = "\033[0m"  # Reset to default
RED = '\033[31m'  # Red color (e.g., for warning or error)
GREEN = '\033[32m'  # Green color (e.g., for success)