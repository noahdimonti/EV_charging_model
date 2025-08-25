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

        # Sum of objectives as a placeholder for the objective function which value will be set later
        # If value is not set than the model is run by the weighted sum method
        self.model.obj_function = pyo.Objective(
            expr=(
                    (self.model.economic_objective / 10) +
                    self.model.technical_objective +
                    self.model.social_objective
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

        # Define objective components
        self.define_objective_components()

    def get_optimisation_model(self):
        return self.model
