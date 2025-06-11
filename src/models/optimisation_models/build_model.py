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
                 version: str,
                 obj_weights: dict):
        self.config = config
        self.charging_strategy = charging_strategy
        self.obj_weights = obj_weights

        self.model = pyo.ConcreteModel(
            name=f'{config.value}_{charging_strategy.value}_{params.num_of_evs}EVs_{version}'
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

        # Define objective function
        def obj_function(model):
            total_objective = 0

            # Economic objective
            if self.obj_weights['economic_weight'] > 0:
                economic_obj = EconomicObjective(model)

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

                total_objective += self.obj_weights['economic_weight'] * economic_cost

            # Technical objective
            if self.obj_weights['technical_weight'] > 0:
                technical_obj = TechnicalObjective(model)

                technical_cost = (
                        technical_obj.f_disc() +
                        technical_obj.f_peak() +
                        technical_obj.f_papr()
                )

                total_objective += self.obj_weights['technical_weight'] * technical_cost

            # Social objective
            if self.obj_weights['social_weight'] > 0:
                social_obj = SocialObjective(model)

                social_cost = (
                        social_obj.f_soc() +
                        social_obj.f_fair()
                )

                total_objective += self.obj_weights['social_weight'] * social_cost

            return total_objective

        self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    def get_optimisation_model(self):
        return self.model
