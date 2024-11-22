import pandas as pd


class ModelOutputs:
    def __init__(self, model_name: str, tariff_type: str, num_of_evs: int, avg_travel_distance: float, min_soc: float):
        # Variables
        self.model_name = model_name
        self.tariff_type = tariff_type
        self.num_of_evs = num_of_evs
        self.avg_travel_distance = avg_travel_distance
        self.min_soc = min_soc

        # Cost metrics
        self.total_optimal_cost = 0.0
        self.investment_maintenance_cost = 0.0
        self.household_load_cost = 0.0
        self.ev_charging_cost = 0.0
        self.grid_import_cost = 0.0
        self.other_costs = 0.0
        self.average_ev_charging_cost = 0.0

        # Power metrics
        self.num_of_households = 0
        self.num_of_cps = 0
        self.max_charging_power = 0.0
        self.peak_ev_load = 0.0
        self.peak_total_demand = 0.0
        self.peak_grid_import = 0.0
        self.avg_daily_peak = 0.0
        self.peak_to_average = 0.0

        # Output dictionary
        self.output_dict = {}


    def calculate_average_ev_charging_cost(self):
        if self.num_of_evs > 0:
            self.average_ev_charging_cost = self.ev_charging_cost / self.num_of_evs

    def to_dict(self):
        # Convert all metrics into a dictionary for storage or DataFrame conversion
        self.output_dict = {
            'Model Name': self.model_name,
            'Tariff type': self.tariff_type,
            'Number of EVs': self.num_of_evs,
            'Average travel distance (km)': self.avg_travel_distance,
            'Minimum SOC (%)': self.min_soc,
            'Number of households': self.num_of_households,
            'Number of CPs': self.num_of_cps,
            'Max charging power (kW)': self.max_charging_power,

            'Total optimal cost ($)': self.total_optimal_cost,
            'Investment & maintenance cost ($)': self.investment_maintenance_cost,
            'Total household load cost ($)': self.household_load_cost,
            'Total EV charging cost ($)': self.ev_charging_cost,
            'Grid import cost ($)': self.grid_import_cost,
            'Other costs ($)': self.other_costs,
            'Average EV charging cost ($)': self.average_ev_charging_cost,

            'Peak EV load (kW)': self.peak_ev_load,
            'Peak total demand (kW)': self.peak_total_demand,
            'Peak grid import (kW)': self.peak_grid_import,
            'Average daily peak (kW)': self.avg_daily_peak,
            'Peak-to-average power ratio (PAPR)': self.peak_to_average
        }

        return self.output_dict

        # return self.__dict__

    def to_dataframe(self):
        # Create dictionary of output
        output_dict = self.to_dict()

        # Extract the model name and remove it from the dictionary
        model_name = output_dict.pop('Model Name')

        # Create a DataFrame where attributes are rows and the model_name is the column header
        idx_col_name = 'Metric'
        df = pd.DataFrame(list(output_dict.items()), columns=[idx_col_name, model_name]).set_index(idx_col_name)

        return df

