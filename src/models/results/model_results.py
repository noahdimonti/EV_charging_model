import pandas as pd
import numpy as np
import pickle
import os
import pyomo.environ as pyo
from collections import defaultdict
from pprint import pprint
from src.config import params, ev_params, independent_variables
from src.models.utils.configs import CPConfig, ChargingStrategy


class ModelResults:
    def __init__(self, model: pyo.ConcreteModel | dict,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy,
                 mip_gap=None):
        self.config = config
        self.charging_strategy = charging_strategy
        self.mip_gap = mip_gap
        self.total_objective_value = None

        self.solver_status: pyo.SolverStatus
        self.termination_condition: pyo.TerminationCondition

        # Extract results from solved model
        # Variables
        self.variables = {}
        if charging_strategy.value == 'uncoordinated':
            self.variables = model
        else:
            for var in model.component_objects(pyo.Var, active=True):
                # Check if the variable has indexes
                if var.is_indexed():
                    self.variables[var.name] = {index: pyo.value(var[index]) for index in var}
                # For scalar variables, store the value directly
                else:
                    self.variables[var.name] = var.value

            # Get objective value
            self.total_objective_value = pyo.value(model.obj_function)

        # Sets
        self.sets = {}
        if charging_strategy.value == 'uncoordinated':
            self.sets = {
                'EV_ID': [_ for _ in range(params.num_of_evs)],
                'TIME': [_ for _ in params.timestamps],
                'DAY': [_ for _ in params.T_d.keys()],
                'WEEK': [_ for _ in params.D_w.keys()]
            }
        else:
            for model_set in model.component_objects(pyo.Set, active=True):
                self.sets[model_set.name] = model_set.data()

        # Objective values
        self.objective_components = {}
        if charging_strategy.value != 'uncoordinated':
            for obj in model.component_objects(pyo.Expression, active=True):
                self.objective_components[obj.name] = pyo.value(obj)

    def get_config_attributes_for_simulation(self) -> dict[str, int | float | dict[int, list]]:
        config_attributes = {
            'p_cp_rated': self.variables['p_cp_rated'] * params.charging_power_resolution_factor,
            'num_cp': None,
            'ev_to_cp_assignment': None
        }

        if self.config.value == 'config_1':
            config_attributes['num_cp'] = int(params.num_of_evs)

        elif self.config.value == 'config_2':
            config_attributes['num_cp'] = int(self.variables['num_cp'])

        elif self.config.value == 'config_3':
            config_attributes['num_cp'] = int(self.variables['num_cp'])

            # Get EV to CP assignment
            ev_to_cp_assignment = defaultdict(list)
            is_ev_permanently_assigned_to_cp = self.variables['is_ev_permanently_assigned_to_cp']
            for (ev_id, cp_id), assigned in is_ev_permanently_assigned_to_cp.items():
                if assigned == 1:
                    ev_to_cp_assignment[cp_id].append(ev_id)

            # Sort dictionary
            ev_to_cp_assignment = dict(sorted(ev_to_cp_assignment.items()))

            config_attributes['ev_to_cp_assignment'] = ev_to_cp_assignment

        return config_attributes

    # Save model as pickle
    def save_model_to_pickle(self, version: str):
        filename = f'{self.config.value}_{self.charging_strategy.value}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
        file_path = os.path.join(params.model_results_folder_path, filename)

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(self, f)

            print(f'Model was successfully saved to: \n{file_path}')

        except Exception as e:
            print(f'Error saving results: {e}')


class EvaluationMetrics:
    def __init__(self, model: ModelResults):
        self.model = model

        self.config = self.model.config
        self.charging_strategy = self.model.charging_strategy
        self.variables = self.model.variables
        self.sets = self.model.sets
        self.mip_gap = self.model.mip_gap
        self.objective_value = self.model.total_objective_value

        # Evaluation metrics initialisation
        # Define number of cp as it varies between configurations
        self.num_cp = None

        if self.config.value == 'config_1':
            self.num_cp = params.num_of_evs
        else:
            self.num_cp = int(self.variables['num_cp'])

        # Define metrics
        self.metrics = {}

        # Collect metrics
        self._collect_metrics()

    # Evaluation metrics methods
    def _investor_metrics(self):
        if self.charging_strategy.value == 'uncoordinated':
            investment_cost = self.num_cp * params.investment_cost[self.variables['p_cp_rated']]

        else:
            investment_cost = self.num_cp * sum(
                params.investment_cost[m] * self.variables['select_cp_rated_power'][m]
                for m in params.p_cp_rated_options_scaled)

        return {
            'investment_cost': investment_cost,
        }

    def _dso_metrics(self):
        household_peak = round(max([params.household_load.loc[t].item() for t in self.sets['TIME']]), 4)
        agg_demand_peak = round(max([self.variables['p_grid'][t] for t in self.sets['TIME']]), 4)
        avg_agg_demand = round(
            np.mean([self.variables['p_grid'][t] for t in self.sets['TIME']]), 4
        )

        p_peak_increase = round(float(
            ((agg_demand_peak - household_peak) / household_peak)
        ), 4) * 100

        papr = round((agg_demand_peak / avg_agg_demand), 4)

        return {
            'p_peak_increase': p_peak_increase,
            'papr': papr
        }

    def _ev_user_metrics(self):
        # Average SOC at departure time
        sum_all_soc_t_dep = sum(
                            (self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i])  # convert SOC to percentage
                            for i in self.sets['EV_ID']
                            for t in ev_params.t_dep_dict[i]
                        )
        total_dep_times = sum(len(ev_params.t_dep_dict[i]) for i in self.sets['EV_ID'])  # total number of dep times for all EVs

        avg_soc_t_dep_percent = round(
                ((sum_all_soc_t_dep / total_dep_times) * 100), 4
        )

        # SOC average deviation from max
        avg_soc_to_max_deviation = 100 - avg_soc_t_dep_percent

        # SOC range
        lowest_soc_percent = min([((self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100)
                                  for i in self.sets['EV_ID']
                                  for t in ev_params.t_dep_dict[i]])

        highest_soc_percent = max([((self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100)
                                   for i in self.sets['EV_ID']
                                   for t in ev_params.t_dep_dict[i]])

        soc_range = highest_soc_percent - lowest_soc_percent

        return {
            'avg_soc_t_dep_percent': avg_soc_t_dep_percent,
            'avg_soc_to_max_deviation': avg_soc_to_max_deviation,
            'soc_range': soc_range
        }

    def _general_metrics(self):
        # Number of CP
        num_cp = self.num_cp

        # Rated power of CP
        p_cp_rated = self.variables['p_cp_rated'] * params.charging_power_resolution_factor

        # Average number of charging days
        avg_num_charging_days = None
        if self.charging_strategy.value == 'uncoordinated' or self.charging_strategy.value == 'opportunistic':
            is_charging_day = {
                (i, d): int(any(self.variables['p_ev'][i, t] > 0 for t in params.T_d[d]))
                for i in self.sets['EV_ID'] for d in self.sets['DAY']
            }

            num_charging_days = {
                (i, w): sum(is_charging_day[i, d] for d in params.D_w[w])
                for i in self.sets['EV_ID'] for w in self.sets['WEEK']
            }

            avg_num_charging_days = sum(
                num_charging_days[i, w] for i in self.sets['EV_ID'] for w in self.sets['WEEK']
            ) / (len(self.sets['EV_ID']) * len(self.sets['WEEK']))

        elif self.charging_strategy.value == 'flexible':
            avg_num_charging_days = pyo.value(
                sum(
                    self.variables['num_charging_days'][i, w]
                    for i in self.sets['EV_ID']
                    for w in self.sets['WEEK'])
            ) / (len(self.sets['EV_ID']) * len(self.sets['WEEK']))

        return {
            'num_cp': num_cp,
            'p_cp_rated': p_cp_rated,
            'avg_num_charging_days': avg_num_charging_days,
        }

    def _collect_metrics(self):
        self.metrics.update(self._investor_metrics())
        self.metrics.update(self._dso_metrics())
        self.metrics.update(self._ev_user_metrics())
        self.metrics.update(self._general_metrics())

        if self.charging_strategy.value != 'uncoordinated':
            self.metrics.update({'total_objective_value': self.objective_value})

        if self.mip_gap is not None:
            self.metrics.update({'mip_gap': self.mip_gap})

        return self.metrics

    # Format metrics
    def format_metrics(self):
        formatted_metrics = {
            'Charging point info': f'{self.metrics['num_cp']} CPs ({self.metrics['p_cp_rated']:,.2f} kW)',

            'Investment cost': f'${self.metrics['investment_cost']:,.2f}',

            'Peak demand increase': f'{self.metrics['p_peak_increase']:,.2f}%',
            'PAPR': f'{self.metrics['papr']:,.2f}',

            'Average SOC at dep time': f'{self.metrics['avg_soc_t_dep_percent']:,.2f}%',
            'Average deviation of SOC at dep time to max SOC': f'{self.metrics['avg_soc_to_max_deviation']:,.2f}%',
            'SOC min-max range': f'{self.metrics['soc_range']:,.2f}%',

            'Average num of charging days': f'{self.metrics['avg_num_charging_days']:,.2f}',

        }

        if self.charging_strategy.value != 'uncoordinated':
            formatted_metrics.update({
                'Optimality gap': f'{self.mip_gap:,.4f}%',
                'Objective value': f'{self.objective_value:,.2f}',

                'Economic objective': f'{self.model.objective_components['economic_objective']:,.2f}',
                'Technical objective': f'{self.model.objective_components['technical_objective']:,.2f}',
                'Social objective': f'{self.model.objective_components['social_objective']:,.2f}',
            })

        return formatted_metrics

    def pprint_metrics(self):
        print(f'\n---------------------------------------------------------')
        print(f'{self.config.value.capitalize()} - {self.charging_strategy.value.capitalize()}'
              f' Charging Evaluation Metrics Summary')
        print(f'\n---------------------------------------------------------')

        pprint(self.format_metrics(), sort_dicts=False)
        print(f'\n---------------------------------------------------------')


def compile_multiple_models_metrics(
        models_metrics: dict,
        filename: str,
        save_df: bool = True) -> pd.DataFrame:
    # Create a list of DataFrames, one for each results
    dfs = [pd.DataFrame(data.values(), index=data.keys(), columns=[model_name])
           for model_name, data in models_metrics.items()]

    # Concatenate all DataFrames along columns
    df = pd.concat(dfs, axis=1)

    # Save compiled dataframe
    if save_df:
        file_path = os.path.join(params.compiled_metrics_folder_path, filename)
        df.to_csv(file_path)

        if 'raw' in filename:
            print(f'\nRaw compiled metrics saved to:\n{file_path}')
        else:
            print(f'\nFormatted compiled metrics saved to:\n{file_path}')

    return df
