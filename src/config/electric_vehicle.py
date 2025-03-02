import pandas as pd
import numpy as np


class ElectricVehicle:
    def __init__(self, timestamps, periods_in_a_day, num_of_days, min_soc, max_soc):
        # Initialize attributes with default values
        self.t_dep = []  # A set of departure times
        self.t_arr = []  # A set of arrival times
        self.travel_energy = []  # Energy consumption values aligning with t_dep and t_arr
        self.travel_energy_t_arr = {}  # Travel energy associated with t_arr (keys: t_arr, values: travel_energy)

        # Parameters passed during initialization
        self.capacity_of_ev = None  # EV battery capacity (kWh)
        self.soc_init = None  # Initial state of charge (kWh)
        self.soc_final = None  # Final state of charge (kWh)
        self.soc_min = min_soc * self.capacity_of_ev  # Minimum state of charge (kWh)
        self.soc_max = max_soc * self.capacity_of_ev  # Maximum state of charge (kWh)

        # DataFrames for SOC, charging power, and at-home status
        self.timestamps = timestamps
        self.soc = pd.DataFrame(index=timestamps, data={'soc': 0.0})
        self.charging_power = pd.DataFrame(index=timestamps, data={'charging_power': 0.0})
        self.at_home_status = pd.DataFrame(index=timestamps, data={'at_home': 0})
