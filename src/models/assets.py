import pyomo.environ as pyo
from enum import Enum
from pprint import pprint


class CPConfig(Enum):
    CONFIG_1 = 'config_1'
    CONFIG_2 = 'config_2'
    CONFIG_3 = 'config_3'

    @classmethod
    def validate(cls, config):
        if config not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as CPConfig.CONFIG_1
            raise ValueError(f"Invalid CP configuration: {config}. Allowed values: {allowed_values}")


class ChargingStrategy(Enum):
    OPPORTUNISTIC = 'opportunistic'
    FLEXIBLE = 'flexible'

    @classmethod
    def validate(cls, charging_strategy):
        if charging_strategy not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as ChargingMode.DAILY_CHARGE
            raise ValueError(f"Invalid CP configuration: {charging_strategy}. Allowed values: {allowed_values}")


class MaxChargingPower(Enum):
    VARIABLE = 'variable'
    L_1_LESS = 1.3
    L_1 = 2.4
    L_2_SINGLE_PHASE = 3.7
    L_2_THREE_PHASE = 7.2

    @classmethod
    def validate(cls, charging_strategy, p_cp_max_mode):
        """Validate p_cp_rated_mode based on charging strategy."""
        if charging_strategy == ChargingStrategy.OPPORTUNISTIC:
            if p_cp_max_mode != cls.VARIABLE:
                raise ValueError(
                    f"For {charging_strategy.value}, p_cp_max must be VARIABLE, not {p_cp_max_mode.value}."
                )
        else:  # Other charging modes
            if p_cp_max_mode == cls.VARIABLE:
                raise ValueError(
                    f"For {charging_strategy.value}, p_cp_max cannot be VARIABLE. Choose a parameter value."
                )


class Grid:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_variables()
        self.initialise_constraints()

    def initialise_variables(self):
        # Grid import power
        self.model.p_grid = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, self.params.P_grid_max))

        # Daily peak and average power
        self.model.p_daily_peak = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.p_daily_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.delta_daily_peak_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)

        # Weekly peak and average power
        self.model.p_weekly_peak = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        self.model.p_weekly_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        self.model.delta_weekly_peak_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)

    def _add_peak_constraints(self, peak_var, avg_var, delta_var, time_sets, index_set, name_prefix):
        """ Generalised function to add peak constraints (daily/weekly). """

        # Peak power constraint
        constraint_list = pyo.ConstraintList()
        setattr(self.model, f"{name_prefix}_peak_power_constraint", constraint_list)

        for idx in index_set:
            for t in time_sets[idx]:
                constraint_list.add(peak_var[idx] >= self.model.p_grid[t])

        # Average peak constraint
        def peak_average_rule(model, idx):
            return avg_var[idx] == (1 / len(time_sets[idx])) * sum(model.p_grid[t] for t in time_sets[idx])

        setattr(self.model, f"{name_prefix}_peak_average_constraint",
                pyo.Constraint(index_set, rule=peak_average_rule))

        # Delta peak constraint
        delta_constraint_list = pyo.ConstraintList()
        setattr(self.model, f"{name_prefix}_delta_peak_avg_constraint", delta_constraint_list)

        for idx in index_set:
            delta_constraint_list.add(delta_var[idx] >= (peak_var[idx] - avg_var[idx]))
            delta_constraint_list.add(delta_var[idx] >= (avg_var[idx] - peak_var[idx]))

    def initialise_constraints(self):
        """ Initialise constraints by calling the generalised function for daily and weekly peaks. """

        # Daily constraints
        self._add_peak_constraints(
            peak_var=self.model.p_daily_peak,
            avg_var=self.model.p_daily_avg,
            delta_var=self.model.delta_daily_peak_avg,
            time_sets=self.params.T_d,
            index_set=self.model.DAY,
            name_prefix="daily"
        )

        # Weekly constraints
        self._add_peak_constraints(
            peak_var=self.model.p_weekly_peak,
            avg_var=self.model.p_weekly_avg,
            delta_var=self.model.delta_weekly_peak_avg,
            time_sets=self.params.T_w,
            index_set=self.model.WEEK,
            name_prefix="weekly"
        )


class HouseholdLoad:
    def __init__(self, model, params):
        self.model = model
        self.params = params

        # Initialise parameter
        self.model.p_household_load = pyo.Param(self.model.TIME, initialize=self.params.household_load)


class CommonConnectionPoint:
    def __init__(self, model, params):
        self.model = model
        self.params = params

    def initialise_constraints(self):
        def energy_balance_rule(model, t):
            # return model.p_grid[t] == model.p_household_load[t] + sum(model.p_cp[j, t] for j in model.CP_ID)
            return model.p_grid[t] == model.p_household_load[t] + sum(model.p_ev[i, t] for i in model.EV_ID)

        self.model.ccp_constraint = pyo.Constraint(self.model.TIME, rule=energy_balance_rule)


class ChargingPoint:
    def __init__(self, model, params, config, charging_strategy, p_cp_max_mode):
        self.model = model
        self.params = params
        self.config = config
        self.charging_strategy = charging_strategy
        self.p_cp_max_mode = p_cp_max_mode
        self.initialise_sets()
        self.initialise_parameters()
        self.initialise_variables()

    def initialise_sets(self):
        if self.config == CPConfig.CONFIG_2:
            self.model.CP_ID = pyo.Set(initialize=range(self.params.num_cp_max))

    def initialise_parameters(self):
        if self.config == CPConfig.CONFIG_1:
            self.model.num_cp = pyo.Param(initialize=len(self.model.EV_ID))

    # --------------------------
    # VARIABLES
    # --------------------------
    def _cp_rated_power_selection_variables(self):
        self.model.p_cp_rated = pyo.Var(within=pyo.NonNegativeReals)
        self.model.select_cp_rated_power = pyo.Var(self.params.p_cp_rated_options_scaled, within=pyo.Binary)

    def _num_cp_decision_variables(self):
        self.model.num_cp = pyo.Var(
            within=pyo.NonNegativeIntegers, bounds=(self.params.num_cp_min, self.params.num_cp_max)
        )
        self.model.cp_is_installed = pyo.Var(
            self.model.CP_ID, within=pyo.Binary
        )
        self.model.p_cp_total = pyo.Var(
            within=pyo.NonNegativeReals
        )

    def initialise_variables(self):
        self._cp_rated_power_selection_variables()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_variables()

    # --------------------------
    # CONSTRAINTS
    # --------------------------
    def _cp_rated_power_selection_constraints(self):
        # Constraint to select optimal rated power of the charging points
        def rated_power_selection(model):
            return model.p_cp_rated == sum(
                model.select_cp_rated_power[m] * m for m in self.params.p_cp_rated_options_scaled
            )

        self.model.rated_power_selection_constraint = pyo.Constraint(rule=rated_power_selection)

        # Constraint to ensure only one rated power variable is selected
        def mutual_exclusivity_rated_power_selection(model):
            return sum(model.select_cp_rated_power[m] for m in self.params.p_cp_rated_options_scaled) == 1

        self.model.mutual_exclusivity_rated_power_selection_constraint = pyo.Constraint(
            rule=mutual_exclusivity_rated_power_selection
        )

    def _num_cp_decision_constraints(self):
        # Constraint: number of CPs built
        def cp_count(model):
            return sum(model.cp_is_installed[j] for j in model.CP_ID) == model.num_cp

        self.model.cp_count_constraint = pyo.Constraint(rule=cp_count)

        # Constraint: ensuring total EV charging demand can be met by the number of installed CPs
        def p_cp_total(model, t):
            return sum(model.p_ev[i, t] for i in model.EV_ID) <= model.p_cp_total

        self.model.p_cp_total_constraint = pyo.Constraint(
            self.model.TIME, rule=p_cp_total
        )

        # The constraint is non-linear, and is linearised below using McCormick relaxation
        def p_cp_total_lb(model):
            return model.p_cp_total >= (self.params.num_cp_min * model.p_cp_rated) + (
                    self.params.p_cp_rated_min * model.num_cp) - (
                    self.params.p_cp_rated_min * self.params.num_cp_min)

        self.model.p_cp_total_lb_constraint = pyo.Constraint(rule=p_cp_total_lb)

        def p_cp_total_ub1(model):
            return model.p_cp_total <= self.params.num_cp_max * model.p_cp_rated

        self.model.p_cp_total_ub1_constraint = pyo.Constraint(rule=p_cp_total_ub1)

        def p_cp_total_ub2(model):
            return model.p_cp_total <= self.params.p_cp_rated_max * model.num_cp

        self.model.p_cp_total_ub2_constraint = pyo.Constraint(rule=p_cp_total_ub2)

    def initialise_constraints(self):
        self._cp_rated_power_selection_constraints()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_constraints()


class ElectricVehicle:
    def __init__(self, model, params, ev_params, config, charging_strategy, p_cp_max_mode):
        self.model = model
        self.params = params
        self.ev_params = ev_params
        self.config = config
        self.charging_strategy = charging_strategy
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

    # --------------------------
    # VARIABLES
    # --------------------------
    def _ev_assignment_variables(self):
        self.model.ev_is_charging_at_cp_j = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, within=pyo.Binary
        )

    def _scheduling_variables(self):
        self.model.num_charging_days = pyo.Var(
            self.model.EV_ID, self.model.WEEK,
            within=pyo.NonNegativeIntegers,
            bounds=(self.params.min_num_charging_days, self.params.max_num_charging_days)
        )
        self.model.is_charging_day = pyo.Var(
            self.model.EV_ID, self.model.DAY, within=pyo.Binary
        )

        if self.config == CPConfig.CONFIG_1:
            self.model.ev_is_charging = pyo.Var(
                self.model.EV_ID, self.model.TIME, within=pyo.Binary
            )

    def initialise_variables(self):
        self.model.p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, None))
        self.model.soc_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals,
                                    bounds=lambda model, i, t: (0, model.soc_max[i]))
        self.model.delta_p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)

        if self.charging_strategy == ChargingStrategy.FLEXIBLE:
            self._scheduling_variables()

        if self.config == CPConfig.CONFIG_2:
            self._ev_assignment_variables()

    # --------------------------
    # CONSTRAINTS
    # --------------------------
    def _soc_constraints(self):
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

    def _charging_discontinuity_constraints(self):
        self.model.charging_discontinuity_constraint = pyo.ConstraintList()

        for i in self.model.EV_ID:
            for t in self.model.TIME:
                if t == self.model.TIME.first():
                    self.model.charging_discontinuity_constraint.add(
                        self.model.delta_p_ev[i, t] == 0
                    )
                else:
                    if self.model.ev_at_home_status[i, t] == 1:
                        self.model.charging_discontinuity_constraint.add(
                            self.model.delta_p_ev[i, t] >=
                            self.model.p_ev[i, t] - self.model.p_ev[i, self.model.TIME.prev(t)]
                        )
                        self.model.charging_discontinuity_constraint.add(
                            self.model.delta_p_ev[i, t] >=
                            self.model.p_ev[i, self.model.TIME.prev(t)] - self.model.p_ev[i, t]
                        )

    def _ev_assignment_constraints(self):
        # Constraint: EVs can only be assigned to existing CPs
        def ev_assigned_to_existing_cp(model, j, t):
            return sum(model.ev_is_charging_at_cp_j[i, j, t] for i in model.EV_ID) <= model.cp_is_installed[j]

        self.model.ev_assigned_to_existing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=ev_assigned_to_existing_cp
        )

    @staticmethod
    def __charging_power_limit_config1_opp(model):
        def upper_bound(model, i, t):
            return model.p_ev[i, t] <= model.ev_at_home_status[i, t] * model.p_cp_rated

        model.upper_bound = pyo.Constraint(
            model.EV_ID, model.TIME, rule=upper_bound
        )

    def __charging_power_limit_config1_flex(self, model):
        def upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=upper_bound1
        )

        def upper_bound2(model, i, t):
            return model.p_ev[i, t] <= self.params.p_cp_rated_max * model.ev_is_charging[i, t]

        model.upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=upper_bound2
        )

        def ev_charges_only_at_home(model, i, t):
            return model.ev_is_charging[i, t] <= model.ev_at_home_status[i, t]

        model.ev_charges_only_at_home_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=ev_charges_only_at_home
        )

    def __charging_power_limit_config2(self, model):
        def upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=upper_bound1
        )

        def upper_bound2(model, i, t):
            return model.p_ev[i, t] <= self.params.p_cp_rated_max * sum(
                model.ev_is_charging_at_cp_j[i, j, t] for j in model.CP_ID
            )

        model.upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=upper_bound2
        )

        def ev_charges_only_at_home(model, i, j, t):
            return model.ev_is_charging_at_cp_j[i, j, t] <= model.ev_at_home_status[i, t]

        model.ev_charges_only_at_home_constraint = pyo.Constraint(
            model.EV_ID, model.CP_ID, model.TIME, rule=ev_charges_only_at_home
        )

    def _charging_power_limit_constraints(self):
        if self.charging_strategy == ChargingStrategy.OPPORTUNISTIC:
            if self.config == CPConfig.CONFIG_1:
                self.__charging_power_limit_config1_opp(self.model)
            elif self.config == CPConfig.CONFIG_2:
                self.__charging_power_limit_config2(self.model)

        elif self.charging_strategy == ChargingStrategy.FLEXIBLE:
            if self.config == CPConfig.CONFIG_1:
                self.__charging_power_limit_config1_flex(self.model)
            elif self.config == CPConfig.CONFIG_2:
                self.__charging_power_limit_config2(self.model)

    def _scheduling_constraints(self):
        def num_charging_days(model, i, w):
            return model.num_charging_days[i, w] == sum(model.is_charging_day[i, d] for d in self.params.D_w[w])

        self.model.num_charging_days_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.WEEK, rule=num_charging_days
        )

        def max_num_charged_evs_daily(model, d):
            return (
                    sum(model.is_charging_day[i, d] for i in model.EV_ID) <=
                    ((self.params.num_of_evs * self.params.max_num_charging_days) / self.params.length_D_w) +
                    self.params.max_charged_evs_daily_margin
            )

        self.model.max_num_charged_evs_daily_constraint = pyo.Constraint(
            self.model.DAY, rule=max_num_charged_evs_daily
        )

        # def charge_only_on_charging_days(model, i, j, d):
        #     # Determine the correct summation based on available indices
        #     if hasattr(model, "ev_is_charging_at_cp_j"):
        #         return (sum(model.ev_is_charging_at_cp_j[i, j, t] for t in self.params.T_d[d])
        #                 <= len(self.params.T_d[d]) * model.is_charging_day[i, d])
        #     else:
        #         return (sum(model.ev_is_charging[i, t] for t in self.params.T_d[d])
        #                 <= len(self.params.T_d[d]) * model.is_charging_day[i, d])
        #
        # self.model.charge_only_on_charging_days_constraint = pyo.Constraint(
        #     self.model.EV_ID, self.model.CP_ID, self.model.DAY, rule=charge_only_on_charging_days
        # )

        def charge_only_on_charging_days(model, i, d, j=None):
            if j is not None:
                # Case: ev_is_charging_at_cp_j (with charging point index)
                return (sum(model.ev_is_charging_at_cp_j[i, j, t] for t in self.params.T_d[d])
                        <= len(self.params.T_d[d]) * model.is_charging_day[i, d])
            else:
                # Case: ev_is_charging (without charging point index)
                return (sum(model.ev_is_charging[i, t] for t in self.params.T_d[d])
                        <= len(self.params.T_d[d]) * model.is_charging_day[i, d])

        # Apply the correct constraint based on whether CP_ID exists
        if hasattr(self.model, 'CP_ID'):
            self.model.charge_only_on_charging_days_constraint = pyo.Constraint(
                self.model.EV_ID, self.model.CP_ID, self.model.DAY,
                rule=lambda model, i, j, d: charge_only_on_charging_days(model, i, d, j)
            )
        else:
            self.model.charge_only_on_charging_days_constraint = pyo.Constraint(
                self.model.EV_ID, self.model.DAY,
                rule=lambda model, i, d: charge_only_on_charging_days(model, i, d)
            )

    def initialise_constraints(self):
        self._soc_constraints()
        self._charging_discontinuity_constraints()
        self._charging_power_limit_constraints()

        if self.charging_strategy == ChargingStrategy.FLEXIBLE:
            self._scheduling_constraints()

        if self.config == CPConfig.CONFIG_2:
            self._ev_assignment_constraints()


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
