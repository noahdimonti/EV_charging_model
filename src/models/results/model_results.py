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
                 obj_weights: dict[str, float],
                 mip_gap=None):
        self.config = config
        self.charging_strategy = charging_strategy
        self.obj_weights = obj_weights
        self.mip_gap = mip_gap

        # Solved model results extraction
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
        avg_p_peak = np.mean(
            [
                max([self.variables['p_grid'][t] for t in params.T_d[d]])
                for d in self.sets['DAY']
            ]
        )
        avg_papr = np.mean(
            [
                (max([self.variables['p_grid'][t] for t in params.T_d[d]]) /
                 np.mean([self.variables['p_grid'][t] for t in params.T_d[d]]))
                for d in self.sets['DAY']
            ]
        )

        avg_daily_peak_increase = np.mean(
            [(max([self.variables['p_grid'][t] for t in params.T_d[d]]) /
              max([params.household_load.loc[t].values for t in params.T_d[d]]))
             for d in self.sets['DAY']]
        )

        return {
            'avg_p_peak': avg_p_peak,
            'avg_papr': avg_papr,
            'avg_daily_peak_increase': avg_daily_peak_increase,
        }

    def _ev_user_metrics(self):
        # User costs
        maintenance_cost = (params.annual_maintenance_cost / 365) * params.num_of_days * self.num_cp
        operational_cost = params.daily_supply_charge_dict[
                               independent_variables.tariff_type] * params.num_of_evs * params.num_of_days
        total_cost_per_user = (sum(
            params.tariff_dict[independent_variables.tariff_type][t] * self.variables['p_ev'][i, t]
            for i in self.sets['EV_ID']
            for t in self.sets['TIME']
        ) + maintenance_cost + operational_cost) / len(self.sets['EV_ID'])

        # SOC metrics
        avg_soc_t_dep_percent = sum(
            (self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) for i in self.sets['EV_ID'] for t in
            ev_params.t_dep_dict[i]
        ) / sum(len(ev_params.t_dep_dict[i]) for i in self.sets['EV_ID']) * 100

        lowest_soc_percent = min([((self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100)
                                  for i in self.sets['EV_ID']
                                  for t in ev_params.t_dep_dict[i]])

        highest_soc_percent = max([((self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100)
                                   for i in self.sets['EV_ID']
                                   for t in ev_params.t_dep_dict[i]])

        soc_range = highest_soc_percent - lowest_soc_percent

        return {
            'total_cost_per_user': total_cost_per_user,
            'avg_soc_t_dep_percent': avg_soc_t_dep_percent,
            'lowest_soc_percent': lowest_soc_percent,
            'highest_soc_percent': highest_soc_percent,
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
        self.metrics.update(self.obj_weights)

        if self.mip_gap is not None:
            self.metrics.update({'mip_gap': self.mip_gap})

        return self.metrics

    # Format metrics
    def format_metrics(self):
        formatted_metrics = {
            'Economic weight': self.obj_weights['economic_weight'],
            'Technical weight': self.obj_weights['technical_weight'],
            'Social weight': self.obj_weights['social_weight'],

            'Investment cost': f'${self.metrics['investment_cost']:,.2f}',

            'Average daily peak': f'{self.metrics['avg_p_peak']:,.3f} kW',
            'Average daily PAPR': f'{self.metrics['avg_papr']:,.3f}',
            'Average daily peak increase from base load': f'{self.metrics['avg_daily_peak_increase']:,.3f}%',

            'Average total cost per user': f'${self.metrics['total_cost_per_user']:,.2f} over {params.num_of_days} days',
            'Average SOC at departure time': f'{self.metrics['avg_soc_t_dep_percent']:,.2f}%',
            'Lowest SOC at departure time': f'{self.metrics['lowest_soc_percent']:,.2f}%',
            'Highest SOC at departure time': f'{self.metrics['highest_soc_percent']:,.2f}%',
            'SOC min-max gap at departure time': f'{self.metrics['soc_range']:,.2f}%',

            'Number of CP': f'{self.metrics['num_cp']} charging points ({self.metrics['p_cp_rated']:,.1f} kW)',
            'Average number of charging days': f'{self.metrics['avg_num_charging_days']:.2f} days per week',
        }

        if self.charging_strategy.value != 'uncoordinated':
            formatted_metrics.update({
                'Optimality gap': f'{self.mip_gap:,.4f}%',
            })

        return formatted_metrics

    def pprint_metrics(self):
        print(f'\n---------------------------------------------------------')
        print(f'{self.config.value.capitalize()} - {self.charging_strategy.value.capitalize()}'
              f' Charging Evaluation Metrics Summary')
        print(f'\n---------------------------------------------------------')

        pprint(self.format_metrics(), sort_dicts=False)
        print(f'\n---------------------------------------------------------')

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


def compile_multiple_models_metrics(models_metrics: dict, filename: str, save_df: bool = True):
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
