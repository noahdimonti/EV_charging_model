import pandas as pd
import numpy as np


class ElectricVehicle:
    def __init__(self, timestamps, periods_in_a_day, num_of_days, min_soc, max_soc):
        # Initialize attributes with default values
        self.at_home_status = pd.DataFrame()  # DataFrame containing timestamps and binaries
        self.soc = pd.DataFrame()  # DataFrame containing timestamps and zeros initially
        self.charging_power = pd.DataFrame()  # DataFrame containing timestamps and zeros initially
        self.t_dep = []  # A set of times of departure
        self.t_arr = []  # A set of times of arrival
        self.travel_energy = []  # Energy consumption values aligning with t_dep and t_arr
        self.travel_energy_t_arr = {}  # Travel energy associated with t_arr (keys: t_arr, values: travel_energy)

        # Parameters passed during initialization
        self.capacity_of_ev = None  # EV battery capacity (kWh)
        self.soc_init = None  # Initial state of charge (kWh)
        self.soc_final = None  # Final state of charge (kWh)
        self.soc_min = min_soc  # Minimum state of charge (kWh)
        self.soc_max = max_soc  # Maximum state of charge (kWh)

        # Create SOC and charging power dataframes
        self.soc = pd.DataFrame({
            'timestamp': timestamps,
            'soc': np.zeros(periods_in_a_day * num_of_days)
        }).set_index('timestamp')

        self.charging_power = pd.DataFrame({
            'timestamp': timestamps,
            'charging_power': np.zeros(periods_in_a_day * num_of_days)
        }).set_index('timestamp')
