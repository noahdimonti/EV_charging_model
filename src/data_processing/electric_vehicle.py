import pandas as pd


class ElectricVehicle:
    def __init__(self, ev_id: int, timestamps):
        self.ev_id = ev_id

        # Attributes related to travel
        self.t_dep = []  # A set of departure times
        self.t_arr = []  # A set of arrival times
        self.travel_energy = []  # Energy consumption values aligning with t_dep and t_arr

        # Attributes related to battery
        self.battery_capacity = None  # EV battery capacity (kWh)
        self.soc_init = None  # Initial state of charge (kWh)
        self.soc_critical = None  # Minimum state of charge (kWh)
        self.soc_max = None  # Maximum state of charge (kWh)

        # DataFrames for at home status, SOC, and charging power
        self.at_home_status = pd.DataFrame(index=timestamps, data={'at_home': 0})
        self.soc = pd.DataFrame(index=timestamps, data={'soc': 0.0})
        self.charging_power = pd.DataFrame(index=timestamps, data={'charging_power': 0.0})
