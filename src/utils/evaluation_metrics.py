import pandas as pd
import numpy as np
import pyomo.environ as pyo
from src.config import params as prm
from src.config import ev_params as ev_prm
from src.config import independent_variables as ind_vars
from src.models.assets import ChargingStrategy
from src.utils import solve_model
from pprint import pprint


class ModelResults:
    def __init__(self, charging_strategy: ChargingStrategy, model, params, ev_params, independent_variables):
        self.charging_strategy = charging_strategy
        self.model = model
        self.params = params
        self.ev_params = ev_params
        self.independent_variables = independent_variables

        # Economic metric variables
        self.investment_cost = None
        self.maintenance_cost = None
        self.operational_cost = None
        self.energy_purchase_cost = None
        self.total_cost = None
        self.avg_num_charging_days = None

        # Technical metric variables
        self.num_cp = None
        self.p_cp_rated = None
        self.avg_p_daily = None
        self.avg_p_peak = None
        self.avg_papr = None

        # Social metric variables
        self.total_ev_charging_cost_per_user = None
        self.avg_daily_ev_charging_cost_per_user = None
        self.avg_soc_t_dep = None
        self.avg_soc_t_dep_percentage = None

    def get_economic_metrics(self):
        # investment cost
        self.investment_cost = self.model.num_cp * sum(self.params.investment_cost[m] * self.model.select_cp_rated_power[m]
                                                  for m in self.params.p_cp_rated_options_scaled)
        self.investment_cost = pyo.value(self.investment_cost)

        # maintenance cost
        self.maintenance_cost = (self.params.annual_maintenance_cost / 365) * self.params.num_of_days * self.model.num_cp

        # operational cost
        self.operational_cost = self.params.daily_supply_charge_dict[self.independent_variables.tariff_type]

        # electricity purchase cost
        self.energy_purchase_cost = sum(
            self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.model.p_grid[t] for t in
            self.model.TIME
        )

        self.total_cost = pyo.value(self.investment_cost + self.maintenance_cost + self.operational_cost + self.energy_purchase_cost)

        return {
            'investment_cost': f'${self.investment_cost:,.2f}',
            'total_cost': f'${self.total_cost:,.2f}',
        }

    def get_technical_metrics(self):
        self.num_cp = pyo.value(self.model.num_cp)
        self.p_cp_rated = pyo.value(self.model.p_cp_rated) * self.params.charging_power_resolution_factor
        self.avg_p_daily = pyo.value(
            np.mean([self.model.p_daily_avg[d] for d in self.model.DAY])
        )
        self.avg_p_peak = pyo.value(
            np.mean([self.model.p_daily_peak[d] for d in self.model.DAY])
        )
        self.avg_papr = pyo.value(
            np.mean([(self.model.p_daily_peak[d] / self.model.p_daily_avg[d]) for d in self.model.DAY])
        )

        return {
            'num_cp': f'{self.num_cp} charging points',
            'p_cp_rated': f'{self.p_cp_rated:,.1f} kW',
            'avg_p_daily': f'{self.avg_p_daily:,.2f} kW',
            'avg_p_peak': f'{self.avg_p_peak:,.2f} kW',
            'avg_papr': f'{self.avg_papr:,.3f}',
        }

    def get_social_metrics(self):
        self.total_ev_charging_cost_per_user = pyo.value(
            sum(
                self.params.tariff_dict[self.independent_variables.tariff_type][t] * self.model.p_ev[i, t]
                for i in self.model.EV_ID
                for t in self.model.TIME
            ) / len(self.model.EV_ID)
        )

        self.avg_daily_ev_charging_cost_per_user = self.total_ev_charging_cost_per_user / len(self.model.DAY)

        self.avg_soc_t_dep = pyo.value(
            sum(
                self.model.soc_ev[i, t] for i in self.model.EV_ID for t in self.ev_params.t_dep_dict[i]
            ) / sum(len(self.ev_params.t_dep_dict[i]) for i in self.model.EV_ID)
        )

        self.avg_soc_t_dep_percentage = pyo.value(
            sum(
                (self.model.soc_ev[i, t] / self.model.soc_max[i]) for i in self.model.EV_ID for t in
                self.ev_params.t_dep_dict[i]
            ) / sum(len(self.ev_params.t_dep_dict[i]) for i in self.model.EV_ID)
        ) * 100

        if self.charging_strategy.value == 'opportunistic':
            is_charging_day = {
                (i, d): int(any(pyo.value(self.model.p_ev[i, t]) > 0 for t in self.params.T_d[d]))
                for i in self.model.EV_ID for d in self.model.DAY
            }

            num_charging_days = {
                (i, w): sum(is_charging_day[i, d] for d in self.params.D_w[w])
                for i in self.model.EV_ID for w in self.model.WEEK
            }

            self.avg_num_charging_days = int(sum(
                num_charging_days[i, w] for i in self.model.EV_ID for w in self.model.WEEK
            ) / (len(self.model.EV_ID) * len(self.model.WEEK)))

        elif self.charging_strategy.value == 'flexible':
            self.avg_num_charging_days = pyo.value(
                sum(
                    self.model.num_charging_days[i, w]
                    for i in self.model.EV_ID
                    for w in self.model.WEEK)
            ) / (len(self.model.EV_ID) * len(self.model.WEEK))

        return {
            'total_ev_charging_cost_per_user': f'${self.total_ev_charging_cost_per_user:,.2f} over {self.params.num_of_days} days',
            'avg_daily_ev_charging_cost': f'${self.avg_daily_ev_charging_cost_per_user:,.2f}',
            'avg_soc_t_dep': f'{self.avg_soc_t_dep:,.2f} kWh',
            'avg_soc_t_dep_percentage': f'{self.avg_soc_t_dep_percentage:,.1f}%',
            'avg_num_charging_days': f'{self.avg_num_charging_days} days per week',
        }
