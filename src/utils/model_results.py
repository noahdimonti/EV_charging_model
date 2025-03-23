import pickle
import pandas as pd
import numpy as np
import pyomo.environ as pyo
from src.config import params


class ModelResults:
    def __init__(self, opt_model, config, charging_strategy, mip_gap):
        self.config = config
        self.charging_strategy = charging_strategy
        self.mip_gap = mip_gap

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

    def save_model_to_pickle(self, file_version: str):
        filename = f'{self.config.value}_{self.charging_strategy.value}_{params.num_of_evs}EVs_{params.num_of_days}days_{file_version}.pkl'
        folder_path = '../../reports/pkl/'
        file_path = folder_path + filename
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)
            print(f'Model saved to {file_path}')

        except Exception as e:
            print(f'Error saving results: {e}')


