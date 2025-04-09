import pyomo.environ as pyo
from src.config import params, independent_variables
from src.models.configs import (
    CPConfig,
    ChargingStrategy
)
from src.models.optimisation_models.assets import (
    Grid,
    HouseholdLoad,
    CommonConnectionPoint,
    ChargingPoint,
    ElectricVehicle
)
from src.models.optimisation_models.objectives import EconomicObjective, TechnicalObjective, SocialObjective


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy):
        self.config = config
        self.charging_strategy = charging_strategy
        self.model = pyo.ConcreteModel(name=f'{config.value}_{charging_strategy.value}_{params.num_of_evs}EVs')
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
            # Economic objective
            economic_obj = EconomicObjective(model)
            economic_cost = economic_obj.investment_cost() + economic_obj.maintenance_cost() + economic_obj.energy_purchase_cost()

            # Technical objective
            technical_obj = TechnicalObjective(model)
            technical_cost = technical_obj.f_disc() + technical_obj.f_peak() + technical_obj.f_papr()

            # Social objective
            social_obj = SocialObjective(model)
            social_cost = social_obj.f_soc()

            return (independent_variables.w_economic * economic_cost) + (
                    independent_variables.w_technical * technical_cost) + (
                    independent_variables.w_social * social_cost)

        self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    def get_optimisation_model(self):
        return self.model
