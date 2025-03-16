import numpy as np
import pyomo.environ as pyo
from src.config import params, ev_params, independent_variables
from src.utils.model_results import ModelResults
from pprint import pprint


class EvaluationMetrics:
    def __init__(self, results: ModelResults):
        self.results = results

        # Extract variables and sets from the model_data
        self.variables = self.results.variables
        self.sets = self.results.sets

        # Define number of cp as it varies between configurations
        self.num_cp = None

        if self.results.config.value == 'config_1':
            self.num_cp = params.num_of_evs
        else:
            self.num_cp = self.variables['num_cp']

        # Define metrics
        self.metrics = {}

        # Collect metrics
        self._collect_metrics()

    def get_economic_metrics(self):
        # investment cost
        investment_cost = self.num_cp * sum(
            params.investment_cost[m] * self.variables['select_cp_rated_power'][m]
            for m in params.p_cp_rated_options_scaled)

        # maintenance cost
        maintenance_cost = (params.annual_maintenance_cost / 365) * params.num_of_days * self.num_cp

        # operational cost
        operational_cost = params.daily_supply_charge_dict[independent_variables.tariff_type]

        # electricity purchase cost
        energy_purchase_cost = sum(
            params.tariff_dict[independent_variables.tariff_type][t] * self.variables['p_grid'][t] for t in
            self.sets['TIME']
        )

        total_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost

        return {
            'investment_cost': investment_cost,
            'total_cost': total_cost,
        }

    def get_technical_metrics(self):
        num_cp = self.num_cp
        p_cp_rated = self.variables['p_cp_rated'] * params.charging_power_resolution_factor
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
            params.tariff_dict[independent_variables.tariff_type][t] * self.variables['p_ev'][i, t]
            for i in self.sets['EV_ID']
            for t in self.sets['TIME']
        ) / len(self.sets['EV_ID'])

        avg_daily_ev_charging_cost_per_user = total_ev_charging_cost_per_user / len(self.sets['DAY'])

        avg_soc_t_dep = sum(
            self.variables['soc_ev'][i, t] for i in self.sets['EV_ID'] for t in ev_params.t_dep_dict[i]
        ) / sum(len(ev_params.t_dep_dict[i]) for i in self.sets['EV_ID'])

        avg_soc_t_dep_percentage = sum(
            (self.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) for i in self.sets['EV_ID'] for t in
            ev_params.t_dep_dict[i]
        ) / sum(len(ev_params.t_dep_dict[i]) for i in self.sets['EV_ID']) * 100

        avg_num_charging_days = None
        if self.results.charging_strategy.value == 'opportunistic':
            is_charging_day = {
                (i, d): int(any(self.variables['p_ev'][i, t] > 0 for t in params.T_d[d]))
                for i in self.sets['EV_ID'] for d in self.sets['DAY']
            }

            num_charging_days = {
                (i, w): sum(is_charging_day[i, d] for d in params.D_w[w])
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

    def _collect_metrics(self):
        self.metrics.update(self.get_economic_metrics())
        self.metrics.update(self.get_technical_metrics())
        self.metrics.update(self.get_social_metrics())

        return self.metrics

    def format_metrics(self):
        formatted_metrics = {
                'investment_cost': f'${self.metrics['investment_cost']:,.2f}',
                'total_cost': f'${self.metrics['total_cost']:,.2f}',

                'num_cp': f'{self.metrics['num_cp']} charging point(s)',
                'p_cp_rated': f'{self.metrics['p_cp_rated']:,.1f} kW',
                'avg_p_daily': f'{self.metrics['avg_p_daily']:,.2f} kW',
                'avg_p_peak': f'{self.metrics['avg_p_peak']:,.2f} kW',
                'avg_papr': f'{self.metrics['avg_papr']:,.3f}',

                'total_ev_charging_cost_per_user': f'${self.metrics['total_ev_charging_cost_per_user']:,.2f} over {params.num_of_days} days',
                'avg_daily_ev_charging_cost_per_user': f'${self.metrics['avg_daily_ev_charging_cost_per_user']:,.2f}',
                'avg_soc_t_dep': f'{self.metrics['avg_soc_t_dep']:,.2f} kWh',
                'avg_soc_t_dep_percentage': f'{self.metrics['avg_soc_t_dep_percentage']:,.1f}%',
                'avg_num_charging_days': f'{self.metrics['avg_num_charging_days']} days per week',
        }

        return formatted_metrics

    def pprint(self):
        pprint(self.format_metrics(), sort_dicts=False)

