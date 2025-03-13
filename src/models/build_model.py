import pyomo.environ as pyo
from configs import (
    CPConfig,
    ChargingStrategy,
    MaxChargingPower
)
from src.models.assets import (
    Grid,
    HouseholdLoad,
    CommonConnectionPoint,
    ChargingPoint,
    ElectricVehicle
)


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_strategy: ChargingStrategy,
                 p_cp_rated_mode: MaxChargingPower,
                 params,
                 ev_params,
                 independent_vars):
        self.config = config
        self.charging_strategy = charging_strategy
        self.p_cp_rated_mode = p_cp_rated_mode
        self.params = params
        self.ev_params = ev_params
        self.independent_vars = independent_vars
        self.model = pyo.ConcreteModel(name=f'{config.value}_{charging_strategy.value}_{self.params.num_of_evs}EVs')
        self.assets = {}

        # Validate configuration and charging mode
        CPConfig.validate(self.config)
        ChargingStrategy.validate(self.charging_strategy)
        # MaxChargingPower.validate(self.charging_strategy, self.p_cp_rated_mode)

        # Set p_cp_rated as variable or parameter
        # if self.p_cp_rated_mode == MaxChargingPower.VARIABLE:
        #     self.model.p_cp_rated = pyo.Var(within=pyo.NonNegativeReals)
        # else:
        #     self.model.p_cp_rated = pyo.Param(
        #         initialize=(float(self.p_cp_rated_mode.value) / self.params.charging_power_resolution_factor),
        #         within=pyo.NonNegativeReals
        #     )

        # Run methods
        self.initialise_sets()
        self.assemble_components()
        self.define_objective()

    def initialise_sets(self):
        self.model.EV_ID = pyo.Set(initialize=[_ for _ in range(self.params.num_of_evs)])

        self.model.TIME = pyo.Set(initialize=self.params.timestamps)
        self.model.DAY = pyo.Set(initialize=[_ for _ in self.params.T_d.keys()])
        self.model.WEEK = pyo.Set(initialize=[_ for _ in self.params.D_w.keys()])

    def assemble_components(self):
        # Initialise assets parameters and variables
        self.assets['grid'] = Grid(self.model, self.params)
        self.assets['household'] = HouseholdLoad(self.model, self.params)
        self.assets['ccp'] = CommonConnectionPoint(self.model, self.params)
        self.assets['cp'] = ChargingPoint(self.model, self.params, self.config, self.charging_strategy,
                                          self.p_cp_rated_mode)
        self.assets['ev'] = ElectricVehicle(self.model, self.params, self.ev_params, self.config,
                                            self.charging_strategy,
                                            self.p_cp_rated_mode)

        # Initialise constraints
        self.assets['ccp'].initialise_constraints()
        self.assets['cp'].initialise_constraints()
        self.assets['ev'].initialise_constraints()

    def define_objective(self):
        def get_economic_cost(model):
            investment_cost = model.num_cp * sum(self.params.investment_cost[m] * model.select_cp_rated_power[m]
                                                 for m in self.params.p_cp_rated_options_scaled)

            maintenance_cost = (self.params.annual_maintenance_cost / 365) * self.params.num_of_days * model.num_cp

            operational_cost = self.params.daily_supply_charge_dict[self.independent_vars.tariff_type]

            energy_purchase_cost = sum(
                self.params.tariff_dict[self.independent_vars.tariff_type][t] * model.p_grid[t] for t in model.TIME
            )

            # total costs
            total_economic_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost

            return total_economic_cost

        def get_technical_cost(model):
            daily_load_variance = sum(model.delta_daily_peak_avg[d] for d in model.DAY)
            weekly_load_variance = sum(model.delta_weekly_peak_avg[w] for w in model.WEEK)
            charging_discontinuity = sum(
                model.delta_p_ev[i, t] for i in model.EV_ID for t in model.TIME
            )

            return daily_load_variance + weekly_load_variance + charging_discontinuity

        def get_social_cost(model):
            return sum(model.soc_max[i] - model.soc_ev[i, t] for i in model.EV_ID for t in self.ev_params.t_dep_dict[i])

        def obj_function(model):
            economic_cost = get_economic_cost(model)
            technical_cost = get_technical_cost(model)
            social_cost = get_social_cost(model)

            return (self.independent_vars.w_economic * economic_cost) + (
                    self.independent_vars.w_technical * technical_cost) + (
                    self.independent_vars.w_social * social_cost)

        self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    def get_model(self):
        return self.model
