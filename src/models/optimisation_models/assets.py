import pyomo.environ as pyo
from src.config import params, ev_params
from src.models.optimisation_models.configs import (
    CPConfig,
    ChargingStrategy
)


class Grid:
    def __init__(self, model):
        self.model = model
        self.initialise_variables()
        # self.initialise_constraints()

    def initialise_variables(self):
        # Grid import power
        self.model.p_grid = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

        # # Daily peak and average power
        # self.model.p_daily_peak = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        # self.model.p_daily_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        # self.model.delta_daily_peak_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        #
        # # Weekly peak and average power
        # self.model.p_weekly_peak = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        # self.model.p_weekly_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        # self.model.delta_weekly_peak_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)

    # def _add_peak_constraints(self, peak_var, avg_var, delta_var, time_sets, index_set, name_prefix):
    #     """ Generalised function to add peak constraints (daily/weekly). """
    #
    #     # Peak power constraint
    #     constraint_list = pyo.ConstraintList()
    #     setattr(self.model, f"{name_prefix}_peak_power_constraint", constraint_list)
    #
    #     for idx in index_set:
    #         for t in time_sets[idx]:
    #             constraint_list.add(peak_var[idx] >= self.model.p_grid[t])
    #
    #     # Average peak constraint
    #     def peak_average_rule(model, idx):
    #         return avg_var[idx] == (1 / len(time_sets[idx])) * sum(model.p_grid[t] for t in time_sets[idx])
    #
    #     setattr(self.model, f"{name_prefix}_peak_average_constraint",
    #             pyo.Constraint(index_set, rule=peak_average_rule))
    #
    #     # Delta peak constraint
    #     delta_constraint_list = pyo.ConstraintList()
    #     setattr(self.model, f"{name_prefix}_delta_peak_avg_constraint", delta_constraint_list)
    #
    #     for idx in index_set:
    #         delta_constraint_list.add(delta_var[idx] >= (peak_var[idx] - avg_var[idx]))
    #         delta_constraint_list.add(delta_var[idx] >= (avg_var[idx] - peak_var[idx]))
    #
    # def initialise_constraints(self):
    #     """ Initialise constraints by calling the generalised function for daily and weekly peaks. """
    #
    #     # Daily constraints
    #     self._add_peak_constraints(
    #         peak_var=self.model.p_daily_peak,
    #         avg_var=self.model.p_daily_avg,
    #         delta_var=self.model.delta_daily_peak_avg,
    #         time_sets=params.T_d,
    #         index_set=self.model.DAY,
    #         name_prefix="daily"
    #     )
    #
    #     # Weekly constraints
    #     self._add_peak_constraints(
    #         peak_var=self.model.p_weekly_peak,
    #         avg_var=self.model.p_weekly_avg,
    #         delta_var=self.model.delta_weekly_peak_avg,
    #         time_sets=params.T_w,
    #         index_set=self.model.WEEK,
    #         name_prefix="weekly"
    #     )


class HouseholdLoad:
    def __init__(self, model):
        self.model = model

        # Initialise parameter
        self.model.p_household_load = pyo.Param(self.model.TIME, initialize=params.household_load)


class CommonConnectionPoint:
    def __init__(self, model):
        self.model = model

    def initialise_constraints(self):
        def energy_balance_rule(model, t):
            return model.p_grid[t] == model.p_household_load[t] + sum(model.p_ev[i, t] for i in model.EV_ID)

        self.model.ccp_constraint = pyo.Constraint(self.model.TIME, rule=energy_balance_rule)


class ChargingPoint:
    def __init__(self, model, config, charging_strategy):
        self.model = model
        self.config = config
        self.charging_strategy = charging_strategy
        self.initialise_sets()
        self.initialise_parameters()
        self.initialise_variables()

    def initialise_sets(self):
        if self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self.model.CP_ID = pyo.Set(initialize=range(params.num_cp_max))

    def initialise_parameters(self):
        if self.config == CPConfig.CONFIG_1:
            self.model.num_cp = pyo.Param(initialize=len(self.model.EV_ID))

    # --------------------------
    # VARIABLES
    # --------------------------
    def _cp_rated_power_selection_variables(self):
        self.model.p_cp_rated = pyo.Var(within=pyo.NonNegativeReals)
        self.model.select_cp_rated_power = pyo.Var(params.p_cp_rated_options_scaled, within=pyo.Binary)

    def _num_cp_decision_variables(self):
        self.model.num_cp = pyo.Var(
            within=pyo.NonNegativeIntegers, bounds=(params.num_cp_min, params.num_cp_max)
        )
        self.model.cp_is_installed = pyo.Var(
            self.model.CP_ID, within=pyo.Binary
        )
        self.model.p_cp_total = pyo.Var(
            within=pyo.NonNegativeReals
        )

    def _config3_variables(self):
        self.model.num_ev_sharing_cp = pyo.Var(self.model.CP_ID, within=pyo.NonNegativeIntegers)
        self.model.ev_is_permanently_assigned_to_cp = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, within=pyo.Binary
        )

    def initialise_variables(self):
        self._cp_rated_power_selection_variables()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_variables()

        elif self.config == CPConfig.CONFIG_3:
            self._num_cp_decision_variables()
            self._config3_variables()

    # --------------------------
    # CONSTRAINTS
    # --------------------------
    def _cp_rated_power_selection_constraints(self):
        # Constraint to select optimal rated power of the charging points
        def rated_power_selection(model):
            return model.p_cp_rated == sum(
                model.select_cp_rated_power[m] * m for m in params.p_cp_rated_options_scaled
            )

        self.model.rated_power_selection_constraint = pyo.Constraint(rule=rated_power_selection)

        # Constraint to ensure only one rated power variable is selected
        def mutual_exclusivity_rated_power_selection(model):
            return sum(model.select_cp_rated_power[m] for m in params.p_cp_rated_options_scaled) == 1

        self.model.mutual_exclusivity_rated_power_selection_constraint = pyo.Constraint(
            rule=mutual_exclusivity_rated_power_selection
        )

    def _num_cp_decision_constraints(self):
        # Constraint: number of CPs built
        def cp_count(model):
            return sum(model.cp_is_installed[j] for j in model.CP_ID) == model.num_cp

        self.model.cp_count_constraint = pyo.Constraint(rule=cp_count)

        # Constraint: ensuring total EV charging demand can be met by the number of installed CPs
        # McCormick relaxation
        def p_cp_total(model, t):
            return sum(model.p_ev[i, t] for i in model.EV_ID) <= model.p_cp_total

        self.model.p_cp_total_constraint = pyo.Constraint(
            self.model.TIME, rule=p_cp_total
        )

        # The constraint is non-linear, and is linearised below using McCormick relaxation
        def p_cp_total_lb(model):
            return model.p_cp_total >= (params.num_cp_min * model.p_cp_rated) + (
                    params.p_cp_rated_min * model.num_cp) - (
                    params.p_cp_rated_min * params.num_cp_min)

        self.model.p_cp_total_lb_constraint = pyo.Constraint(rule=p_cp_total_lb)

        def p_cp_total_ub1(model):
            return model.p_cp_total <= params.num_cp_max * model.p_cp_rated

        self.model.p_cp_total_ub1_constraint = pyo.Constraint(rule=p_cp_total_ub1)

        def p_cp_total_ub2(model):
            return model.p_cp_total <= params.p_cp_rated_max * model.num_cp

        self.model.p_cp_total_ub2_constraint = pyo.Constraint(rule=p_cp_total_ub2)

    def _ev_cp_permanent_assignment_constraints(self):
        # Constraint: number of EVs sharing one CP
        def num_ev_sharing_cp(model, j):
            return sum(model.ev_is_permanently_assigned_to_cp[i, j] for i in model.EV_ID) <= model.num_ev_sharing_cp[j]

        self.model.num_ev_sharing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_sharing_cp
        )

        # Constraint: each EV can only be assigned to one CP
        def ev_to_cp_mutual_exclusivity(model, i):
            return sum(model.ev_is_permanently_assigned_to_cp[i, j] for j in model.CP_ID) == 1

        self.model.ev_to_cp_mutual_exclusivity_constraint = pyo.Constraint(
            self.model.EV_ID, rule=ev_to_cp_mutual_exclusivity
        )

        # Constraint: EVs can only be connected to its assigned CP
        def ev_cp_connection(model, i, j, t):
            return model.ev_is_connected_to_cp_j[i, j, t] <= model.ev_is_permanently_assigned_to_cp[i, j]

        self.ev_cp_connection_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=ev_cp_connection
        )

    def _num_ev_per_cp_limit_constraints(self):
        # def num_ev_per_cp_lower_bound(model_data, j):
        #     return model_data.num_ev_sharing_cp[j] >= (params.num_of_evs / model_data.num_cp) - 1
        #
        # self.model_data.num_ev_per_cp_lower_bound_constraint = pyo.Constraint(
        #     self.model_data.CP_ID, rule=num_ev_per_cp_lower_bound
        # )
        #
        # def num_ev_per_cp_upper_bound(model_data, j):
        #     return model_data.num_ev_sharing_cp[j] <= (params.num_of_evs / model_data.num_cp) + 1
        #
        # self.model_data.num_ev_per_cp_upper_bound_constraint = pyo.Constraint(
        #     self.model_data.CP_ID, rule=num_ev_per_cp_upper_bound
        # )

        def num_ev_per_cp_limit(model, j):
            return model.num_ev_sharing_cp[j] <= params.num_of_evs

        self.model.num_ev_per_cp_limit_constraints = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_per_cp_limit
        )

    def _evs_share_installed_cp_constraints(self):
        # Big M linearisation
        def evs_share_installed_cp_upper_bound(model, j):
            return model.num_ev_sharing_cp[j] <= params.num_of_evs * model.cp_is_installed[j]

        self.model.evs_share_installed_cp_upper_bound_constraint = pyo.Constraint(
            self.model.CP_ID, rule=evs_share_installed_cp_upper_bound
        )

        def total_num_ev_share(model):
            return sum(model.num_ev_sharing_cp[j] for j in model.CP_ID) == params.num_of_evs

        self.model.total_num_ev_share_constraint = pyo.Constraint(rule=total_num_ev_share)

    def initialise_constraints(self):
        self._cp_rated_power_selection_constraints()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_constraints()

        elif self.config == CPConfig.CONFIG_3:
            self._num_cp_decision_constraints()
            self._ev_cp_permanent_assignment_constraints()
            self._num_ev_per_cp_limit_constraints()
            self._evs_share_installed_cp_constraints()


class ElectricVehicle:
    def __init__(self, model, config, charging_strategy):
        self.model = model
        self.config = config
        self.charging_strategy = charging_strategy
        self.initialise_parameters()
        self.initialise_variables()

    def initialise_parameters(self):
        self.model.soc_critical = pyo.Param(self.model.EV_ID, initialize=ev_params.soc_critical_dict)
        self.model.soc_max = pyo.Param(self.model.EV_ID, initialize=ev_params.soc_max_dict)
        self.model.soc_init = pyo.Param(self.model.EV_ID, initialize=ev_params.soc_init_dict)
        self.model.ev_at_home_status = pyo.Param(self.model.EV_ID, self.model.TIME,
                                                 initialize=lambda model, i, t:
                                                 ev_params.at_home_status_dict[i].loc[t, f'EV_ID{i}'],
                                                 within=pyo.Binary)

    # --------------------------
    # VARIABLES
    # --------------------------
    def _ev_assignment_variables(self):
        self.model.ev_is_connected_to_cp_j = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, within=pyo.Binary
        )

    def _scheduling_variables(self):
        self.model.num_charging_days = pyo.Var(
            self.model.EV_ID, self.model.WEEK,
            within=pyo.NonNegativeIntegers,
            bounds=(params.min_num_charging_days, params.max_num_charging_days)
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
        # self.model.delta_p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)

        if self.charging_strategy == ChargingStrategy.FLEXIBLE:
            self._scheduling_variables()

        if self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self._ev_assignment_variables()

    # --------------------------
    # CONSTRAINTS
    # --------------------------
    def _soc_constraints(self):
        def get_trip_number_k(i, t):
            if t in ev_params.t_arr_dict[i]:
                k = ev_params.t_arr_dict[i].index(t)
            elif t in ev_params.t_dep_dict[i]:
                k = ev_params.t_dep_dict[i].index(t)
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
            elif t in ev_params.t_arr_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] - ev_params.travel_energy_dict[i][
                    k]

            # otherwise soc follows regular charging constraint
            else:
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] + (
                        ev_params.charging_efficiency * model.p_ev[i, t])

        self.model.soc_evolution = pyo.Constraint(self.model.EV_ID, self.model.TIME, rule=soc_evolution)

        def minimum_required_soc_at_departure(model, i, t):
            # SOC required before departure time
            if t in ev_params.t_dep_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] >= model.soc_critical[i] + ev_params.travel_energy_dict[i][k]
            return pyo.Constraint.Skip

        self.model.minimum_required_soc_at_departure_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.TIME, rule=minimum_required_soc_at_departure
        )

        def final_soc_rule(model, i):
            return model.soc_ev[i, model.TIME.last()] >= model.soc_init[i]

        self.model.final_soc_constraint = pyo.Constraint(self.model.EV_ID, rule=final_soc_rule)

    # def _charging_discontinuity_constraints(self):
    #     self.model.charging_discontinuity_constraint = pyo.ConstraintList()
    #
    #     for i in self.model.EV_ID:
    #         for t in self.model.TIME:
    #             if t == self.model.TIME.first():
    #                 self.model.charging_discontinuity_constraint.add(
    #                     self.model.delta_p_ev[i, t] == 0
    #                 )
    #             else:
    #                 if self.model.ev_at_home_status[i, t] == 1:
    #                     self.model.charging_discontinuity_constraint.add(
    #                         self.model.delta_p_ev[i, t] >=
    #                         self.model.p_ev[i, t] - self.model.p_ev[i, self.model.TIME.prev(t)]
    #                     )
    #                     self.model.charging_discontinuity_constraint.add(
    #                         self.model.delta_p_ev[i, t] >=
    #                         self.model.p_ev[i, self.model.TIME.prev(t)] - self.model.p_ev[i, t]
    #                     )

    def _ev_assignment_and_mutual_exclusivity_constraints_config_2_3(self):
        # Constraint: EVs can only be assigned to existing CPs
        def ev_assigned_to_existing_cp(model, j, t):
            return sum(model.ev_is_connected_to_cp_j[i, j, t] for i in model.EV_ID) <= model.cp_is_installed[j]

        self.model.ev_assigned_to_existing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=ev_assigned_to_existing_cp
        )

    @staticmethod
    def __charging_power_limit_config1_opp(model):
        def charging_power_limit_config1__opp_upper_bound(model, i, t):
            return model.p_ev[i, t] <= model.ev_at_home_status[i, t] * model.p_cp_rated

        model.charging_power_limit_config1__opp_upper_bound_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1__opp_upper_bound
        )

    def __charging_power_limit_config1_flex(self, model):
        def charging_power_limit_config1_flex_upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.charging_power_limit_config1_flex_upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1_flex_upper_bound1
        )

        def charging_power_limit_config1_flex_upper_bound2(model, i, t):
            return model.p_ev[i, t] <= params.p_cp_rated_max * model.ev_is_charging[i, t]

        model.charging_power_limit_config1_flex_upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1_flex_upper_bound2
        )

        def ev_charges_only_at_home(model, i, t):
            return model.ev_is_charging[i, t] <= model.ev_at_home_status[i, t]

        model.ev_charges_only_at_home_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=ev_charges_only_at_home
        )

    def __charging_power_limit_config_2_3(self, model):
        # Big M linearisation
        def charging_power_limit_config_2_3_upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.charging_power_limit_config_2_3_upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config_2_3_upper_bound1
        )

        def charging_power_limit_config_2_3_upper_bound2(model, i, t):
            return model.p_ev[i, t] <= params.p_cp_rated_max * sum(
                model.ev_is_connected_to_cp_j[i, j, t] for j in model.CP_ID
            )

        model.charging_power_limit_config_2_3_upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config_2_3_upper_bound2
        )

        def ev_charges_only_at_home(model, i, j, t):
            return model.ev_is_connected_to_cp_j[i, j, t] <= model.ev_at_home_status[i, t]

        model.ev_charges_only_at_home_constraint = pyo.Constraint(
            model.EV_ID, model.CP_ID, model.TIME, rule=ev_charges_only_at_home
        )

    def _charging_power_limit_constraints(self):
        if self.config == CPConfig.CONFIG_1:
            if self.charging_strategy == ChargingStrategy.OPPORTUNISTIC:
                self.__charging_power_limit_config1_opp(self.model)
            elif self.charging_strategy == ChargingStrategy.FLEXIBLE:
                self.__charging_power_limit_config1_flex(self.model)

        elif self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self.__charging_power_limit_config_2_3(self.model)

    def _scheduling_constraints(self):
        def num_charging_days(model, i, w):
            return model.num_charging_days[i, w] == sum(model.is_charging_day[i, d] for d in params.D_w[w])

        self.model.num_charging_days_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.WEEK, rule=num_charging_days
        )

        def max_num_charged_evs_daily(model, d):
            return (
                    sum(model.is_charging_day[i, d] for i in model.EV_ID) <=
                    ((params.num_of_evs * params.max_num_charging_days) / params.length_D_w) +
                    params.max_charged_evs_daily_margin
            )

        self.model.max_num_charged_evs_daily_constraint = pyo.Constraint(
            self.model.DAY, rule=max_num_charged_evs_daily
        )

        # def charge_only_on_charging_days(model_data, i, j, d):
        #     # Determine the correct summation based on available indices
        #     if hasattr(model_data, "ev_is_connected_to_cp_j"):
        #         return (sum(model_data.ev_is_connected_to_cp_j[i, j, t] for t in self.params.T_d[d])
        #                 <= len(self.params.T_d[d]) * model_data.is_charging_day[i, d])
        #     else:
        #         return (sum(model_data.ev_is_charging[i, t] for t in self.params.T_d[d])
        #                 <= len(self.params.T_d[d]) * model_data.is_charging_day[i, d])
        #
        # self.model_data.charge_only_on_charging_days_constraint = pyo.Constraint(
        #     self.model_data.EV_ID, self.model_data.CP_ID, self.model_data.DAY, rule=charge_only_on_charging_days
        # )

        def charge_only_on_charging_days(model, i, d, j=None):
            if j is not None:
                # Case: ev_is_connected_to_cp_j (with charging point index)
                return (sum(model.ev_is_connected_to_cp_j[i, j, t] for t in params.T_d[d])
                        <= len(params.T_d[d]) * model.is_charging_day[i, d])
            else:
                # Case: ev_is_charging (without charging point index)
                return (sum(model.ev_is_charging[i, t] for t in params.T_d[d])
                        <= len(params.T_d[d]) * model.is_charging_day[i, d])

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

        if self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self._ev_assignment_and_mutual_exclusivity_constraints_config_2_3()
