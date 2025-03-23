import pyomo.environ as pyo
from src.config import params, ev_params, independent_variables
from src.models.optimisation_models.configs import (
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
            technical_cost = technical_obj.f_papr() + technical_obj.f_peak() + technical_obj.f_disc()

            # Social objective
            social_obj = SocialObjective(model)
            social_cost = social_obj.f_soc() + social_obj.f_fair()

            return (independent_variables.w_economic * economic_cost) + (
                    independent_variables.w_technical * technical_cost) + (
                    independent_variables.w_social * social_cost)

        self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    # def define_objective(self):
    #     def get_economic_cost(model):
    #         investment_cost = model.num_cp * sum(params.investment_cost[m] * model.select_cp_rated_power[m]
    #                                              for m in params.p_cp_rated_options_scaled)
    #
    #         maintenance_cost = (params.annual_maintenance_cost / 365) * params.num_of_days * model.num_cp
    #
    #         operational_cost = params.daily_supply_charge_dict[independent_variables.tariff_type]
    #
    #         energy_purchase_cost = sum(
    #             params.tariff_dict[independent_variables.tariff_type][t] * model.p_grid[t] for t in model.TIME
    #         )
    #
    #         # total costs
    #         total_economic_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost
    #
    #         return total_economic_cost
    #
    #     def get_technical_cost(model):
    #         daily_load_variance = sum(model.delta_daily_peak_avg[d] for d in model.DAY)
    #         weekly_load_variance = sum(model.delta_weekly_peak_avg[w] for w in model.WEEK)
    #         charging_discontinuity = sum(
    #             model.delta_p_ev[i, t] for i in model.EV_ID for t in model.TIME
    #         )
    #
    #         return daily_load_variance + weekly_load_variance + charging_discontinuity
    #
    #     def get_social_cost(model):
    #         return sum(model.soc_max[i] - model.soc_ev[i, t] for i in model.EV_ID for t in ev_params.t_dep_dict[i])
    #
    #     def obj_function(model):
    #         economic_cost = get_economic_cost(model)
    #         technical_cost = get_technical_cost(model)
    #         social_cost = get_social_cost(model)
    #
    #         return (independent_variables.w_economic * economic_cost) + (
    #                 independent_variables.w_technical * technical_cost) + (
    #                 independent_variables.w_social * social_cost)
    #
    #     self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)
    def get_optimisation_model(self):
        return self.model
