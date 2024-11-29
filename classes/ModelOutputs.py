import pandas as pd


class ModelOutputs:
    def __init__(self, model_name: str, tariff_type: str, num_of_evs: int, avg_travel_distance: float, min_soc: float):
        # Variables
        self.model_name = model_name
        self.tariff_type = tariff_type
        self.num_of_evs = num_of_evs
        self.avg_travel_distance = avg_travel_distance
        self.min_soc = min_soc
        self.n_connected_ev = pd.Series()

        # Cost metrics
        self.total_cost = 0.0
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
        self.total_ev_load = 0.0
        self.peak_ev_load = 0.0
        self.peak_total_demand = 0.0
        self.peak_grid_import = 0.0
        self.avg_daily_peak = 0.0
        self.peak_to_average = 0.0
        self.ev_load = pd.Series()

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
            'Average travel distance (km)': f'{self.avg_travel_distance} km',
            'Minimum SOC (%)': f'{int(self.min_soc * 100)}%',
            'Number of households': self.num_of_households,
            'Number of CPs': self.num_of_cps,
            'Max charging power (kW)': f'{self.max_charging_power:,.2f} kW',

            'Total cost ($)': f'${self.total_cost:,.2f}',
            'Investment & maintenance cost ($)': f'${self.investment_maintenance_cost:,.2f}',
            'Total household load cost ($)': f'${self.household_load_cost:,.2f}',
            'Total EV charging cost ($)': f'${self.ev_charging_cost:,.2f}',
            'Grid import cost ($)': f'${self.grid_import_cost:,.2f}',
            'Other costs ($)': f'${self.other_costs:,.2f}',
            'Average EV charging cost ($)': f'${self.average_ev_charging_cost:,.2f}',

            'Total EV load (kW)': f'{self.total_ev_load:,.2f} kW',
            'Peak EV load (kW)': f'{self.peak_ev_load:,.2f} kW',
            'Peak total demand (kW)': f'{self.peak_total_demand:,.2f} kW',
            'Peak grid import (kW)': f'{self.peak_grid_import:,.2f} kW',
            'Average daily peak (kW)': f'{self.avg_daily_peak:,.2f} kW',
            'Peak-to-average power ratio (PAPR)': f'{self.peak_to_average:,.2f}'
        }

        return self.output_dict

    def to_dataframe(self):
        # Create dictionary of output
        output_dict = self.to_dict()

        # Extract the model name and remove it from the dictionary
        model_name = output_dict.pop('Model Name').replace("'", "")

        # Create a DataFrame where attributes are rows and the model_name is the column header
        idx_col_name = 'Metric'
        df = pd.DataFrame(list(output_dict.items()), columns=[idx_col_name, model_name]).set_index(idx_col_name)

        return df

