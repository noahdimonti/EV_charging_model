import pandas as pd
import numpy as np
import pyomo.environ as pyo
from src.config import params as prm
from src.config import ev_params as ev_prm
from src.config import independent_variables as ind_vars
from src.models.build_model import CPConfig, ChargingStrategy
from src.utils import solve_model
from src.utils.save_results import Results
from pprint import pprint


class EvaluationMetrics:
    def __init__(self, results: Results, params, ev_params, independent_variables):
        self.results = results
        self.params = params
        self.ev_params = ev_params
        self.independent_variables = independent_variables

        # Extract variables and sets from the model_data
        self.variables = self.results.variables
        self.sets = self.results.sets

        # Define number of cp as it varies between configurations
        self.num_cp = None

        if self.results.config.value == 'config_1':
            self.num_cp = self.params.num_of_evs
        else:
            self.num_cp = self.variables['num_cp']

        # Define metrics
        self.metrics = {}

        # Collect metrics
        self.collect_metrics()

    def get_economic_metrics(self):
        # investment cost
        investment_cost = self.num_cp * sum(
            self.params.investment_cost[m] * self.variables['select_cp_rated_power'][m]
            for m in self.params.p_cp_rated_options_scaled)

        # maintenance cost
        maintenance_cost = (self.params.annual_maintenance_cost / 365) * self.params.num_of_days * self.num_cp

        # operational cost
        operational_cost = self.params.daily_supply_charge_dict[self.independent_variables.tariff_type]

        # electricity purchase cost
        energy_purchase_cost = sum(
            self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.variables['p_grid'][t] for t in
            self.sets['TIME']
        )

        total_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost

        return {
            'investment_cost': investment_cost,
            'total_cost': total_cost,
        }

    def get_technical_metrics(self):
        num_cp = self.num_cp
        p_cp_rated = self.variables['p_cp_rated'] * self.params.charging_power_resolution_factor
        avg_p_daily = np.mean(
            [self.variables['p_daily_avg'][d] for d in self.sets['DAY']]
        )
        avg_p_peak = np.mean(
            [self.variables['p_daily_peak'][d] for d in self.sets['DAY']]
        )
        avg_papr = np.mean(
            [(self.variables['p_daily_peak'][d] / self.variables['p_daily_avg'][d]) for d in self.sets['DAY']]
        )

        return {
            'num_cp': num_cp,
            'p_cp_rated': p_cp_rated,
            'avg_p_daily': avg_p_daily,
            'avg_p_peak': avg_p_peak,
            'avg_papr': avg_papr,
        }

    def get_social_metrics(self):
        total_ev_charging_cost_per_user = sum(
            self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.variables['p_ev'][i, t]
            for i in self.sets['EV_ID']
            for t in self.sets['TIME']
        ) / len(self.sets['EV_ID'])

        avg_daily_ev_charging_cost_per_user = total_ev_charging_cost_per_user / len(self.sets['DAY'])

        avg_soc_t_dep = sum(
            self.variables['soc_ev'][i, t] for i in self.sets['EV_ID'] for t in self.ev_params.t_dep_dict[i]
        ) / sum(len(self.ev_params.t_dep_dict[i]) for i in self.sets['EV_ID'])

        avg_soc_t_dep_percentage = sum(
            (self.variables['soc_ev'][i, t] / self.ev_params.soc_max_dict[i]) for i in self.sets['EV_ID'] for t in
            self.ev_params.t_dep_dict[i]
        ) / sum(len(self.ev_params.t_dep_dict[i]) for i in self.sets['EV_ID']) * 100

        avg_num_charging_days = None
        if self.results.charging_strategy.value == 'opportunistic':
            is_charging_day = {
                (i, d): int(any(self.variables['p_ev'][i, t] > 0 for t in self.params.T_d[d]))
                for i in self.sets['EV_ID'] for d in self.sets['DAY']
            }

            num_charging_days = {
                (i, w): sum(is_charging_day[i, d] for d in self.params.D_w[w])
                for i in self.sets['EV_ID'] for w in self.sets['WEEK']
            }

            avg_num_charging_days = int(sum(
                num_charging_days[i, w] for i in self.sets['EV_ID'] for w in self.sets['WEEK']
            ) / (len(self.sets['EV_ID']) * len(self.sets['WEEK'])))

        elif self.results.charging_strategy.value == 'flexible':
            avg_num_charging_days = pyo.value(
                sum(
                    self.variables['num_charging_days'][i, w]
                    for i in self.sets['EV_ID']
                    for w in self.sets['WEEK'])
            ) / (len(self.sets['EV_ID']) * len(self.sets['WEEK']))

        return {
            'total_ev_charging_cost_per_user': total_ev_charging_cost_per_user,
            'avg_daily_ev_charging_cost_per_user': avg_daily_ev_charging_cost_per_user,
            'avg_soc_t_dep': avg_soc_t_dep,
            'avg_soc_t_dep_percentage': avg_soc_t_dep_percentage,
            'avg_num_charging_days': avg_num_charging_days,
        }

    def collect_metrics(self):
        self.metrics.update(self.get_economic_metrics())
        self.metrics.update(self.get_technical_metrics())
        self.metrics.update(self.get_social_metrics())

        return self.metrics

    def pprint(self):
        pprint(
            {
                'economic_metrics': {
                    'investment_cost': f'${self.metrics['investment_cost']:,.2f}',
                    'total_cost': f'${self.metrics['total_cost']:,.2f}',
                },
                'technical_metrics': {
                    'num_cp': f'{self.metrics['num_cp']} charging point(s)',
                    'p_cp_rated': f'{self.metrics['p_cp_rated']:,.1f} kW',
                    'avg_p_daily': f'{self.metrics['avg_p_daily']:,.2f} kW',
                    'avg_p_peak': f'{self.metrics['avg_p_peak']:,.2f} kW',
                    'avg_papr': f'{self.metrics['avg_papr']:,.3f}',
                },
                'social_metrics': {
                    'total_ev_charging_cost_per_user': f'${self.metrics['total_ev_charging_cost_per_user']:,.2f} over {self.params.num_of_days} days',
                    'avg_daily_ev_charging_cost_per_user': f'${self.metrics['avg_daily_ev_charging_cost_per_user']:,.2f}',
                    'avg_soc_t_dep': f'{self.metrics['avg_soc_t_dep']:,.2f} kWh',
                    'avg_soc_t_dep_percentage': f'{self.metrics['avg_soc_t_dep_percentage']:,.1f}%',
                    'avg_num_charging_days': f'{self.metrics['avg_num_charging_days']} days per week',
                }
            }
        )
# class EvaluationMetrics:
#     def __init__(self, charging_strategy, model_data, params, ev_params, independent_variables):
#         self.charging_strategy = charging_strategy
#         self.model_data = model_data
#         self.params = params
#         self.ev_params = ev_params
#         self.independent_variables = independent_variables
#
#         # Store all metrics in a unified dictionary
#         self.metrics = {}
#
#     def _get_value(self, expression):
#         """Helper function to safely evaluate Pyomo expressions."""
#         return pyo.value(expression)
#
#     def compute_economic_metrics(self):
#         """Calculate economic metrics."""
#         investment_cost = self._get_value(
#             self.model_data.num_cp * sum(
#                 self.params.investment_cost[m] * self.model_data.select_cp_rated_power[m]
#                 for m in self.params.p_cp_rated_options_scaled
#             )
#         )
#         maintenance_cost = self.params.annual_maintenance_cost / 365 * self.params.num_of_days * self.model_data.num_cp
#         operational_cost = self.params.daily_supply_charge_dict[self.independent_variables.tariff_type]
#         energy_purchase_cost = sum(
#             self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.model_data.p_grid[t]
#             for t in self.model_data.TIME
#         )
#
#         total_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost
#
#         return {
#             'investment_cost': investment_cost,
#             'maintenance_cost': maintenance_cost,
#             'operational_cost': operational_cost,
#             'energy_purchase_cost': energy_purchase_cost,
#             'total_cost': total_cost
#         }
#
#     def compute_technical_metrics(self):
#         """Calculate technical metrics."""
#         num_cp = int(self._get_value(self.model_data.num_cp))
#         p_cp_rated = self._get_value(self.model_data.p_cp_rated) * self.params.charging_power_resolution_factor
#         avg_p_daily = self._get_value(np.mean([self.model_data.p_daily_avg[d] for d in self.model_data.DAY]))
#         avg_p_peak = self._get_value(np.mean([self.model_data.p_daily_peak[d] for d in self.model_data.DAY]))
#         avg_papr = self._get_value(np.mean([(self.model_data.p_daily_peak[d] / self.model_data.p_daily_avg[d]) for d in self.model_data.DAY]))
#
#         return {
#             'num_cp': num_cp,
#             'p_cp_rated': p_cp_rated,
#             'avg_p_daily': avg_p_daily,
#             'avg_p_peak': avg_p_peak,
#             'avg_papr': avg_papr
#         }
#
#     def compute_social_metrics(self):
#         """Calculate social metrics."""
#         total_ev_charging_cost_per_user = self._get_value(
#             sum(
#                 self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.model_data.p_ev[i, t]
#                 for i in self.model_data.EV_ID
#                 for t in self.model_data.TIME
#             ) / len(self.model_data.EV_ID)
#         )
#         avg_daily_ev_charging_cost_per_user = total_ev_charging_cost_per_user / len(self.model_data.DAY)
#
#         avg_soc_t_dep = self._get_value(
#             sum(self.model_data.soc_ev[i, t] for i in self.model_data.EV_ID for t in self.ev_params.t_dep_dict[i]) /
#             sum(len(self.ev_params.t_dep_dict[i]) for i in self.model_data.EV_ID)
#         )
#
#         avg_soc_t_dep_percentage = avg_soc_t_dep * 100
#
#         return {
#             'total_ev_charging_cost_per_user': total_ev_charging_cost_per_user,
#             'avg_daily_ev_charging_cost_per_user': avg_daily_ev_charging_cost_per_user,
#             'avg_soc_t_dep': avg_soc_t_dep,
#             'avg_soc_t_dep_percentage': avg_soc_t_dep_percentage
#         }
#
#     def collect_metrics(self):
#         """Collect all metrics from each category."""
#         self.metrics.update(self.compute_economic_metrics())
#         self.metrics.update(self.compute_technical_metrics())
#         self.metrics.update(self.compute_social_metrics())
#         return self.metrics
#
#     def get_metrics_as_dataframe(self, model_name):
#         """Return metrics as a DataFrame for easier comparison across models."""
#         self.collect_metrics()
#         return pd.DataFrame(self.metrics, index=[model_name])
#
#     def display_metrics(self):
#         pprint(self.metrics)
