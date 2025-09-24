from poplib import error_proto

import pyomo.environ as pyo
import os
from src.config import params
from src.models.utils.configs import (
    CPConfig,
    ChargingStrategy
)
from src.models.optimisation_models.assets.grid import Grid
from src.models.optimisation_models.assets.household_load import HouseholdLoad
from src.models.optimisation_models.assets.common_connection_point import CommonConnectionPoint
from src.models.optimisation_models.assets.charging_point import ChargingPoint
from src.models.optimisation_models.assets.electric_vehicle import ElectricVehicle
from src.models.optimisation_models.objectives import EconomicObjective, TechnicalObjective, SocialObjective

from data.outputs.metrics.compiled_metrics.payoff_table import payoff_table


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy,
                 version: str,
                 obj_weights: dict[str, int|float]):
        self.config = config
        self.charging_strategy = charging_strategy
        self.version = version
        self.obj_weights = obj_weights

        self.model = pyo.ConcreteModel(
            name=f'{config.value}_{charging_strategy.value}_{params.num_of_evs}EVs_{self.version}'
        )
        self.assets = {}

        # Validate configuration and charging mode
        CPConfig.validate(self.config)
        ChargingStrategy.validate(self.charging_strategy)

        # Run methods
        self.initialise_sets()
        self.assemble_components()

    def initialise_sets(self):
        self.model.EV_ID = pyo.Set(initialize=[_ for _ in range(params.num_of_evs)])
        self.model.TIME = pyo.Set(initialize=params.timestamps)
        self.model.DAY = pyo.Set(initialize=[_ for _ in params.T_d.keys()])
        self.model.WEEK = pyo.Set(initialize=[_ for _ in params.D_w.keys()])

    def _normalise_cost(self, obj_expr, name):
        payoff = payoff_table[f'{self.config.value}_{self.charging_strategy.value}']
        min_val = payoff[f'{name}_min']
        max_val = payoff[f'{name}_max']
        scaling_constant = 100

        return (obj_expr - min_val) / (max_val - min_val) * scaling_constant

    def define_objective_components(self):
        # Economic objective
        economic_obj = EconomicObjective(self.model)

        investment_cost = (
            economic_obj.investment_cost()
            if self.config.value == 'config_1'
            else economic_obj.investment_cost_linearised()
        )

        economic_cost = (
                investment_cost +
                economic_obj.maintenance_cost() +
                economic_obj.energy_purchase_cost()
        )

        # self.model.economic_objective = pyo.Expression(expr=economic_cost)
        self.model.economic_objective = pyo.Expression(expr=economic_cost / 10)

        # Technical objective
        technical_obj = TechnicalObjective(self.model)

        technical_cost = (
                technical_obj.f_disc() +
                technical_obj.f_peak() +
                technical_obj.f_papr()
        )

        self.model.technical_objective = pyo.Expression(expr=technical_cost)

        # Social objective
        social_obj = SocialObjective(self.model)

        social_cost = (
                social_obj.f_soc() +
                social_obj.f_fair()
        )

        self.model.social_objective = pyo.Expression(expr=social_cost)


        # Normalise objectives
        norm_economic_cost = self._normalise_cost(economic_cost, 'economic')
        self.model.norm_economic_objective = pyo.Expression(expr=norm_economic_cost)

        norm_technical_cost = self._normalise_cost(technical_cost, 'technical')
        self.model.norm_technical_objective = pyo.Expression(expr=norm_technical_cost)

        norm_social_cost = self._normalise_cost(social_cost, 'social')
        self.model.norm_social_objective = pyo.Expression(expr=norm_social_cost)


        # Objective formulation
        self.model.obj_function = pyo.Objective(
            expr=(
                    # self.obj_weights['economic'] * self.model.norm_economic_objective +
                    # self.obj_weights['technical'] * self.model.norm_technical_objective +
                    # self.obj_weights['social'] * self.model.norm_social_objective

                    self.obj_weights['economic'] * self.model.economic_objective +
                    self.obj_weights['technical'] * self.model.technical_objective +
                    self.obj_weights['social'] * self.model.social_objective
            ),
            sense=pyo.minimize
        )

        # Total sum of the objectives
        self.model.total_objective_value = pyo.Expression(
            expr=(self.model.economic_objective + self.model.technical_objective + self.model.social_objective)
        )

    def assemble_components(self):
        # Initialise assets parameters and variables
        self.assets['grid'] = Grid(self.model)
        self.assets['household'] = HouseholdLoad(self.model)
        self.assets['ccp'] = CommonConnectionPoint(self.model)
        self.assets['cp'] = ChargingPoint(self.model, self.config, self.charging_strategy)
        self.assets['ev'] = ElectricVehicle(self.model, self.config,
                                            self.charging_strategy)

        # Initialise constraints
        self.assets['ccp'].initialise_constraints()
        self.assets['cp'].initialise_constraints()
        self.assets['ev'].initialise_constraints()

        # Define objective components
        self.define_objective_components()

    def get_optimisation_model(self):
        return self.model

