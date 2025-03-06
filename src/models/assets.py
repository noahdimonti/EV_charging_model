import pyomo.environ as pyo
from enum import Enum
from pprint import pprint


class Grid:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_variables()

    def initialise_variables(self):
        # Grid import power
        self.model.p_grid = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, self.params.P_grid_max))

        # Peak and average power
        self.model.p_peak = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.p_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.delta_peak_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)

    def initialise_constraints(self):
        self.model.peak_power_constraint = pyo.ConstraintList()

        for d in self.model.DAY:
            for t in self.params.T_d[d]:
                self.model.peak_power_constraint.add(self.model.p_peak[d] >= self.model.p_grid[t])

        def peak_average(model, d):
            return model.p_avg[d] == (1 / len(self.params.T_d[d])) * sum(model.p_grid[t] for t in self.params.T_d[d])

        self.model.peak_average_constraint = pyo.Constraint(
            self.model.DAY, rule=peak_average
        )

        self.model.delta_peak_average_constraint = pyo.ConstraintList()

        for d in self.model.DAY:
            self.model.delta_peak_average_constraint.add(
                self.model.delta_peak_avg[d] >= (self.model.p_peak[d] - self.model.p_avg[d]))
            self.model.delta_peak_average_constraint.add(
                self.model.delta_peak_avg[d] >= (self.model.p_avg[d] - self.model.p_peak[d]))


class HouseholdLoad:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_parameters()

    def initialise_parameters(self):
        self.model.p_household_load = pyo.Param(self.model.TIME, initialize=self.params.household_load)


class CommonConnectionPoint:
    def __init__(self, model, params):
        self.model = model
        self.params = params

    def initialise_constraints(self):
        def energy_balance_rule(model, t):
            return model.p_grid[t] == model.p_household_load[t] + sum(model.p_cp[j, t] for j in model.CP_ID)

        self.model.ccp_constraint = pyo.Constraint(self.model.TIME, rule=energy_balance_rule)


class CPConfig(Enum):
    CONFIG_1 = 'config_1'
    CONFIG_2 = 'config_2'
    CONFIG_3 = 'config_3'

    @classmethod
    def validate(cls, config):
        if config not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as CPConfig.CONFIG_1
            raise ValueError(f"Invalid CP configuration: {config}. Allowed values: {allowed_values}")


class ChargingMode(Enum):
    DAILY_CHARGE = 'daily_charge'
    FLEXIBLE_WEEKLY = 'flexible_weekly'

    @classmethod
    def validate(cls, charging_mode):
        if charging_mode not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as ChargingMode.DAILY_CHARGE
            raise ValueError(f"Invalid CP configuration: {charging_mode}. Allowed values: {allowed_values}")


class MaxChargingPower(Enum):
    VARIABLE = 'variable'
    L_1_LESS = 1.3
    L_1 = 2.4
    L_2_SINGLE_PHASE = 3.7
    L_2_THREE_PHASE = 7.2

    @classmethod
    def validate(cls, charging_mode, p_cp_max_mode):
        """Validate p_cp_max_mode based on charging_mode."""
        if charging_mode == ChargingMode.DAILY_CHARGE:
            if p_cp_max_mode != cls.VARIABLE:
                raise ValueError(
                    f"For {charging_mode.value}, p_cp_max must be VARIABLE, not {p_cp_max_mode.value}."
                )
        else:  # Other charging modes
            if p_cp_max_mode == cls.VARIABLE:
                raise ValueError(
                    f"For {charging_mode.value}, p_cp_max cannot be VARIABLE. Choose a parameter value."
                )


class ChargingPoint:
    def __init__(self, model, params, config, charging_mode, p_cp_max_mode):
        self.model = model
        self.params = params
        self.config = config
        self.charging_mode = charging_mode
        self.p_cp_max_mode = p_cp_max_mode
        self.initialise_sets()
        self.initialise_variables()

    def initialise_sets(self):
        if self.config == CPConfig.CONFIG_1:
            self.model.CP_ID = pyo.Set(initialize=[_ for _ in range(self.params.num_of_evs)])

    def initialise_variables(self):
        self.model.p_cp = pyo.Var(self.model.CP_ID, self.model.TIME, within=pyo.NonNegativeReals)

        if self.config == CPConfig.CONFIG_1 and self.charging_mode == ChargingMode.DAILY_CHARGE:
            self.model.select_cp_rated_power = pyo.Var(self.params.p_cp_max_options_scaled, within=pyo.Binary)

    def initialise_constraints(self):
        if self.config == CPConfig.CONFIG_1 and self.charging_mode == ChargingMode.DAILY_CHARGE:
            # Constraint to select optimal rated power of the charging points
            def rated_power_selection(model):
                return model.p_cp_max == sum(
                    model.select_cp_rated_power[m] * m for m in self.params.p_cp_max_options_scaled
                )

            self.model.rated_power_selection_constraint = pyo.Constraint(rule=rated_power_selection)

            # Constraint to ensure only one rated power variable is selected
            def mutual_exclusivity_rated_power_selection(model):
                return sum(model.select_cp_rated_power[m] for m in self.params.p_cp_max_options_scaled) == 1

            self.model.mutual_exclusivity_rated_power_selection_constraint = pyo.Constraint(
                rule=mutual_exclusivity_rated_power_selection
            )

            # CP power limits
            self.model.cp_power_limits_constraint = pyo.ConstraintList()

            for j in self.model.CP_ID:
                for t in self.model.TIME:
                    self.model.cp_power_limits_constraint.add(self.model.p_cp[j, t] >= 0)
                    self.model.cp_power_limits_constraint.add(self.model.p_cp[j, t] <= self.model.p_cp_max)

            # CP-EV relationship
            def cp_ev_relationship(model, i, j, t):
                return model.p_ev[i, t] == model.p_cp[j, t]

            self.model.cp_ev_relationship_constraint = pyo.Constraint(
                self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=cp_ev_relationship
            )


class ElectricVehicle:
    def __init__(self, model, params, ev_params, config, charging_mode, p_cp_max_mode):
        self.model = model
        self.params = params
        self.ev_params = ev_params
        self.config = config
        self.charging_mode = charging_mode
        self.p_cp_max_mode = p_cp_max_mode
        self.initialise_parameters()
        self.initialise_variables()

    def initialise_parameters(self):
        self.model.soc_critical = pyo.Param(self.model.EV_ID, initialize=self.ev_params.soc_critical_dict)
        self.model.soc_max = pyo.Param(self.model.EV_ID, initialize=self.ev_params.soc_max_dict)
        self.model.soc_init = pyo.Param(self.model.EV_ID, initialize=self.ev_params.soc_init_dict)

        self.model.ev_at_home_status = pyo.Param(self.model.EV_ID, self.model.TIME,
                                                 initialize=lambda model, i, t:
                                                 self.ev_params.at_home_status_dict[i].loc[t, f'EV_ID{i}'],
                                                 within=pyo.Binary)

    def initialise_variables(self):
        self.model.p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)
        self.model.soc_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals,
                                    bounds=lambda model, i, t: (0, model.soc_max[i]))

    def initialise_soc_constraints(self):
        def get_trip_number_k(i, t):
            if t in self.ev_params.t_arr_dict[i]:
                k = self.ev_params.t_arr_dict[i].index(t)
            elif t in self.ev_params.t_dep_dict[i]:
                k = self.ev_params.t_dep_dict[i].index(t)
            else:
                return None
            return k

        self.model.soc_limits_constraint = pyo.ConstraintList()

        for i in self.model.EV_ID:
            for t in self.model.TIME:
                self.model.soc_limits_constraint.add(self.model.soc_ev[i, t] <= self.model.soc_max[i])
                self.model.soc_limits_constraint.add(self.model.soc_ev[i, t] >= self.model.soc_critical[i])

        def soc_evolution(model, i, t):
            # set initial soc
            if t == model.TIME.first():
                return model.soc_ev[i, t] == model.soc_init[i]

            # constraint to set ev soc at arrival time
            elif t in self.ev_params.t_arr_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] - self.ev_params.travel_energy_dict[i][
                    k]

            # otherwise soc follows regular charging constraint
            else:
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] + (
                        self.ev_params.charging_efficiency * model.p_ev[i, t])

        self.model.soc_evolution = pyo.Constraint(self.model.EV_ID, self.model.TIME, rule=soc_evolution)

        def minimum_required_soc_at_departure(model, i, t):
            # SOC required before departure time
            if t in self.ev_params.t_dep_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] >= model.soc_critical[i] + self.ev_params.travel_energy_dict[i][k]
            return pyo.Constraint.Skip

        self.model.minimum_required_soc_at_departure_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.TIME, rule=minimum_required_soc_at_departure
        )

        def final_soc_rule(model, i):
            return model.soc_ev[i, model.TIME.last()] >= model.soc_init[i]

        self.model.final_soc_constraint = pyo.Constraint(self.model.EV_ID, rule=final_soc_rule)

    def initialise_ev_charging_power_constraints(self):
        self.model.ev_charging_power_limit_constraints = pyo.ConstraintList()

        if self.config == CPConfig.CONFIG_1:
            if self.charging_mode == ChargingMode.DAILY_CHARGE:
                for i in self.model.EV_ID:
                    for t in self.model.TIME:
                        self.model.ev_charging_power_limit_constraints.add(
                            self.model.p_ev[i, t] >= 0
                        )
                        self.model.ev_charging_power_limit_constraints.add(
                            self.model.p_ev[i, t] <= self.model.ev_at_home_status[i, t] * self.model.p_cp_max
                        )

            elif self.charging_mode == ChargingMode.FLEXIBLE_WEEKLY:
                # Define new variables and parameters
                self.model.ev_is_charging = pyo.Var(
                    self.model.EV_ID, self.model.TIME, within=pyo.Binary
                )
                self.model.num_charging_days = pyo.Var(
                    self.model.EV_ID, self.model.WEEK,
                    within=pyo.Integers,
                    bounds=(self.params.min_num_charging_days, self.params.max_num_charging_days)
                )
                # self.model.highest_num_charging_days = pyo.Var(
                #     self.model.WEEK, within=pyo.Integers
                # )
                self.model.is_charging_day = pyo.Var(
                    self.model.EV_ID, self.model.DAY, within=pyo.Binary
                )

                # Define scheduling constraints
                for i in self.model.EV_ID:
                    for t in self.model.TIME:
                        self.model.ev_charging_power_limit_constraints.add(
                            self.model.p_ev[i, t] >= 0
                        )
                        self.model.ev_charging_power_limit_constraints.add(
                            self.model.p_ev[i, t] <= self.model.ev_is_charging[i, t] * self.model.p_cp_max
                        )
                        self.model.ev_charging_power_limit_constraints.add(
                            self.model.ev_is_charging[i, t] <= self.model.ev_at_home_status[i, t]
                        )

                def charge_only_on_charging_days(model, i, d):
                    return (sum(model.ev_is_charging[i, t] for t in self.params.T_d[d]) <=
                            len(self.params.T_d[d]) * model.is_charging_day[i, d])

                self.model.charge_only_on_charging_days_constraint = pyo.Constraint(
                    self.model.EV_ID, self.model.DAY, rule=charge_only_on_charging_days
                )

                def num_charging_days(model, i, w):
                    return model.num_charging_days[i, w] == sum(model.is_charging_day[i, d] for d in self.params.D_w[w])

                self.model.num_charging_days_constraint = pyo.Constraint(
                    self.model.EV_ID, self.model.WEEK, rule=num_charging_days
                )

                # self.model.highest_num_charging_days_constraint = pyo.ConstraintList()
                #
                # for w in self.model.WEEK:
                #     for i in self.model.EV_ID:
                #         self.model.highest_num_charging_days_constraint.add(
                #             self.model.highest_num_charging_days[w] >= self.model.num_charging_days[i, w]
                #         )

                def max_num_charged_evs_daily(model, d):
                    return (
                            sum(model.is_charging_day[i, d] for i in model.EV_ID) <=
                            ((self.params.num_of_evs * self.params.max_num_charging_days) / self.params.length_D_w) +
                            self.params.max_charged_evs_daily_margin
                    )

                self.model.max_num_charged_evs_daily_constraint = pyo.Constraint(
                    self.model.DAY, rule=max_num_charged_evs_daily
                )

    def initialise_base_constraints(self):
        self.initialise_soc_constraints()
        self.initialise_ev_charging_power_constraints()


class BuildModel:
    def __init__(self,
                 config: CPConfig,
                 charging_mode: ChargingMode,
                 p_cp_max_mode: MaxChargingPower,
                 params,
                 ev_params,
                 independent_vars):
        self.config = config
        self.charging_mode = charging_mode
        self.p_cp_max_mode = p_cp_max_mode
        self.params = params
        self.ev_params = ev_params
        self.independent_vars = independent_vars
        self.model = pyo.ConcreteModel(name=f'{config.value}_{charging_mode.value}')
        self.assets = {}

        # Validate configuration and charging mode
        CPConfig.validate(self.config)
        ChargingMode.validate(self.charging_mode)
        MaxChargingPower.validate(self.charging_mode, self.p_cp_max_mode)

        # Set p_cp_max as variable or parameter
        if self.p_cp_max_mode == MaxChargingPower.VARIABLE:
            self.model.p_cp_max = pyo.Var(within=pyo.NonNegativeReals)
        else:
            self.model.p_cp_max = pyo.Param(
                initialize=(float(self.p_cp_max_mode.value) / self.params.charging_power_resolution_factor),
                within=pyo.NonNegativeReals
            )

        # Run methods
        self.initialise_sets()
        self.assemble_components()
        self.define_objective()

    def initialise_sets(self):
        self.model.TIME = pyo.Set(initialize=self.params.timestamps)
        self.model.EV_ID = pyo.Set(initialize=[_ for _ in range(self.params.num_of_evs)])

        self.model.DAY = pyo.Set(initialize=[_ for _ in self.params.T_d.keys()])
        self.model.WEEK = pyo.Set(initialize=[_ for _ in self.params.D_w.keys()])

    def assemble_components(self):
        # Initialise assets parameters and variables
        self.assets['grid'] = Grid(self.model, self.params)
        self.assets['household'] = HouseholdLoad(self.model, self.params)
        self.assets['ccp'] = CommonConnectionPoint(self.model, self.params)
        self.assets['cp'] = ChargingPoint(self.model, self.params, self.config, self.charging_mode, self.p_cp_max_mode)
        self.assets['ev'] = ElectricVehicle(self.model, self.params, self.ev_params, self.config, self.charging_mode, self.p_cp_max_mode)

        # Initialise constraints
        self.assets['grid'].initialise_constraints()
        self.assets['ccp'].initialise_constraints()
        self.assets['cp'].initialise_constraints()
        self.assets['ev'].initialise_base_constraints()

    def define_objective(self):
        def get_economic_cost(model):
            # investment cost
            if self.p_cp_max_mode == MaxChargingPower.VARIABLE:
                investment_cost = len(model.CP_ID) * sum(self.params.investment_cost[m] * model.select_cp_rated_power[m]
                                                         for m in self.params.p_cp_max_options_scaled)
            else:
                investment_cost = len(model.CP_ID) * self.params.investment_cost[self.model.p_cp_max.value]

            # maintenance cost per charging point for the duration
            maintenance_cost = (self.params.annual_maintenance_cost / 365) * self.params.num_of_days * len(model.CP_ID)

            # operational cost
            operational_cost = self.params.daily_supply_charge_dict[self.independent_vars.tariff_type]

            # electricity purchase cost
            energy_purchase_cost = sum(
                self.params.tariff_dict[self.independent_vars.tariff_type][t] * model.p_grid[t] for t in model.TIME
            )

            # total costs
            total_economic_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost

            return total_economic_cost

        def get_load_cost(model):
            return sum(model.delta_peak_avg[d] for d in model.DAY)

        def get_soc_cost(model):
            return sum(model.soc_max[i] - model.soc_ev[i, t] for i in model.EV_ID for t in self.ev_params.t_dep_dict[i])

        def obj_function(model):
            economic_cost = get_economic_cost(model)
            load_cost = get_load_cost(model)
            soc_cost = get_soc_cost(model)

            return (self.independent_vars.w_cost * economic_cost) + (self.independent_vars.w_load * load_cost) + (
                    self.independent_vars.w_soc * soc_cost)

        self.model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    def get_model(self):
        return self.model
