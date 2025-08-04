import pyomo.environ as pyo
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


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy,
                 version: str):
        self.config = config
        self.charging_strategy = charging_strategy
        self.version = version

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

        self.model.economic_objective = pyo.Expression(expr=economic_cost)

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

        self.model.obj_function = pyo.Objective(
            expr=(
                    0.4 * self.model.economic_objective +
                    0.4 * self.model.technical_objective +
                    0.2 * self.model.social_objective
            ),
            sense=pyo.minimize
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

        # Define objective
        self.define_objective_components()

        # Epsilon constraints
        epsilon_placeholder = 1e6
        # econ_obj_max = 17259.90
        # tech_obj_max = 1338.05
        # soc_obj_max = 1971.98

        econ_obj_max = 1
        tech_obj_max = 1
        soc_obj_max = 1

        self.model.economic_epsilon_constraint = pyo.Constraint(
            expr=(self.model.economic_objective / econ_obj_max) <= epsilon_placeholder
        )

        self.model.technical_epsilon_constraint = pyo.Constraint(
            expr=(self.model.technical_objective / tech_obj_max) <= epsilon_placeholder
        )

        self.model.social_epsilon_constraint = pyo.Constraint(
            expr=(self.model.social_objective / soc_obj_max) <= epsilon_placeholder
        )

        self.model.obj_function = pyo.Objective(
            expr=(
                    self.model.economic_objective
                 # + self.model.technical_objective
            ),
            sense=pyo.minimize
        )

        # epsilon_placeholder = 1e6
        # self.model.economic_epsilon_constraint = pyo.Constraint(
        #     expr=self.model.economic_objective <= epsilon_placeholder
        # )
        #
        # self.model.technical_epsilon_constraint = pyo.Constraint(
        #     expr=self.model.technical_objective <= epsilon_placeholder
        # )
        #
        # self.model.social_epsilon_constraint = pyo.Constraint(
        #     expr=self.model.social_objective <= epsilon_placeholder
        # )
        #
        # self.model.obj_function = pyo.Objective(
        #     expr=self.model.economic_objective,
        #     sense=pyo.minimize
        # )

    def get_optimisation_model(self):
        return self.model
