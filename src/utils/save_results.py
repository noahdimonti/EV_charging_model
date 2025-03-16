import pickle
import pandas as pd
import numpy as np
import pyomo.environ as pyo


class Results:
    def __init__(self, opt_model, config, charging_strategy):
        self.config = config
        self.charging_strategy = charging_strategy

        self.variables = {}
        for var in opt_model.component_objects(pyo.Var, active=True):
            # Check if the variable has indexes
            if var.is_indexed():
                self.variables[var.name] = {index: pyo.value(var[index]) for index in var}
            # For scalar variables, store the value directly
            else:
                self.variables[var.name] = var.value

        self.sets = {}
        for model_set in opt_model.component_objects(pyo.Set, active=True):
            self.sets[model_set.name] = model_set.data()

    def save_model_to_pickle(self, filename='model_results.pkl'):
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self, f)
            print(f'Model saved to {filename}')

        except Exception as e:
            print(f'Error saving results: {e}')


def save_eval_metrics_individual_result(metrics_data: dict, filename: str):
    # Save to a json file
    with open(f'../../reports/{filename}.json', 'w') as f:
        json.dump(metrics_data, f, indent=4)


def compile_results_from_multiple_models(metrics_data: dict, filename: str):
    flattened_metrics = {**metrics_data["economic_metrics"],
                         **metrics_data["technical_metrics"],
                         **metrics_data["social_metrics"]}

    # Create a DataFrame where each column represents a model_data's metrics
    # df = pd.DataFrame({model_name: flatten_metrics(metrics) for model_name, metrics in model_results.items()})
    #
    # print(df)

    return flattened_metrics


model_results = {
    "model_A": {
        "economic_metrics": {
            "investment_cost": "$6,000.00",
            "total_cost": "$25,951.16"
        },
        "technical_metrics": {
            "avg_p_daily": "78.42 kW",
            "avg_p_peak": "137.24 kW",
            "avg_papr": "1.748",
            "num_cp": "4 charging point(s)",
            "p_cp_rated": "7.2 kW"
        },
        "social_metrics": {
            "avg_daily_ev_charging_cost": "$3.57",
            "avg_num_charging_days": "5 days per week",
            "avg_soc_t_dep": "35.45 kWh",
            "avg_soc_t_dep_percentage": "89.1%",
            "total_ev_charging_cost_per_user": "$25.02 over 7 days"
        }
    },
    "model_B": {
        "economic_metrics": {
            "investment_cost": "$5,500.00",
            "total_cost": "$24,500.00"
        },
        "technical_metrics": {
            "avg_p_daily": "75.00 kW",
            "avg_p_peak": "130.00 kW",
            "avg_papr": "1.733",
            "num_cp": "4 charging point(s)",
            "p_cp_rated": "7.2 kW"
        },
        "social_metrics": {
            "avg_daily_ev_charging_cost": "$3.40",
            "avg_num_charging_days": "4 days per week",
            "avg_soc_t_dep": "34.00 kWh",
            "avg_soc_t_dep_percentage": "85.0%",
            "total_ev_charging_cost_per_user": "$23.80 over 7 days"
        }
    }
}

# Flatten metrics for each model_data
def flatten_metrics(model_data):
    return {**model_data["economic_metrics"],
            **model_data["technical_metrics"],
            **model_data["social_metrics"]}

# print({**model_results['model_A']['economic_metrics']})

# Create a DataFrame where each column represents a model_data's metrics
df = pd.DataFrame({model_name: flatten_metrics(metrics) for model_name, metrics in model_results.items()})

# print(df)