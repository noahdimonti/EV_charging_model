import pyomo.environ as pyo
from src.config import params, ev_params
from src.models.configs import (
    CPConfig,
    ChargingStrategy
)


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
        self.model.is_ev_permanently_assigned_to_cp = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, within=pyo.Binary
        )

        self.model.is_ev_cp_connected = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, within=pyo.Binary
        )

        self.model.p_ev_cp = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, within=pyo.NonNegativeReals
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
            self.model.is_ev_charging = pyo.Var(
                self.model.EV_ID, self.model.TIME, within=pyo.Binary
            )

    def initialise_variables(self):
        self.model.p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, None))
        self.model.soc_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals,
                                    bounds=lambda model, i, t: (0, model.soc_max[i]))

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

    def _ev_assignment_and_mutual_exclusivity_constraints_config_2_3(self):
        # Constraint: EVs can only be assigned to existing CPs and only one EV can charge at each CP
        def ev_assigned_to_existing_cp(model, j, t):
            return sum(model.is_ev_cp_connected[i, j, t] for i in model.EV_ID) <= model.is_cp_installed[j]

        self.model.ev_assigned_to_existing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=ev_assigned_to_existing_cp
        )

    @staticmethod
    def __charging_power_limit_config1_opp(model):
        def charging_power_limit_config1_opp_upper_bound(model, i, t):
            return model.p_ev[i, t] <= model.ev_at_home_status[i, t] * model.p_cp_rated

        model.charging_power_limit_config1_opp_upper_bound_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1_opp_upper_bound
        )

    def __charging_power_limit_config1_flex(self, model):
        def charging_power_limit_config1_flex_upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.charging_power_limit_config1_flex_upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1_flex_upper_bound1
        )

        def charging_power_limit_config1_flex_upper_bound2(model, i, t):
            return model.p_ev[i, t] <= params.p_cp_rated_max * model.is_ev_charging[i, t]

        model.charging_power_limit_config1_flex_upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config1_flex_upper_bound2
        )

        def ev_charges_only_at_home(model, i, t):
            return model.is_ev_charging[i, t] <= model.ev_at_home_status[i, t]

        model.ev_charges_only_at_home_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=ev_charges_only_at_home
        )

    def __charging_power_limit_config_2_3(self, model):
        '''
        # Big M linearisation
        bigM = params.p_cp_rated_max
        def charging_power_limit_config_2_3_upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.charging_power_limit_config_2_3_upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config_2_3_upper_bound1
        )

        def charging_power_limit_config_2_3_upper_bound2(model, i, t):
            return model.p_ev[i, t] <= bigM * sum(
                model.is_ev_cp_connected[i, j, t] for j in model.CP_ID
            )

        model.charging_power_limit_config_2_3_upper_bound2_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config_2_3_upper_bound2
        )
        '''

        def charging_power_limit_config3(model, i, t):
            return model.p_ev[i, t] <= sum(model.is_ev_cp_connected[i, j, t] for j in model.CP_ID) * model.p_cp_rated

        model.charging_power_limit_config3_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config3
        )

        # Constraint: EVs can only be connected to its assigned CP and when it is at home
        def ev_cp_connection(model, i, j, t):
            return (model.is_ev_cp_connected[i, j, t] <=
                    model.is_ev_permanently_assigned_to_cp[i, j] * model.ev_at_home_status[i, t])

        model.ev_cp_connection_constraint = pyo.Constraint(
            model.EV_ID, model.CP_ID, model.TIME, rule=ev_cp_connection
        )

        # Constraint: ensuring total EV charging demand can be met by the number of installed CPs
        def p_cp_total(model, t):
            return sum(model.p_ev[i, t] for i in model.EV_ID) <= model.num_cp * model.p_cp_rated

        self.model.p_cp_total_constraint = pyo.Constraint(
            self.model.TIME, rule=p_cp_total
        )
        '''
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
        '''

        # New constraints
        # Link EV total power to CP-specific power
        def ev_power_sum_rule(model, i, t):
            return model.p_ev[i, t] == sum(model.p_ev_cp[i, j, t] for j in model.CP_ID)

        self.model.ev_power_sum = pyo.Constraint(
            self.model.EV_ID, self.model.TIME, rule=ev_power_sum_rule
        )

        # Power is only nonzero if connected AND permanently assigned
        def cp_power_limit_rule(model, i, j, t):
            return model.p_ev_cp[i, j, t] <= model.p_cp_rated * model.is_ev_cp_connected[i, j, t]

        self.model.cp_power_limit = pyo.Constraint(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=cp_power_limit_rule
        )

    def _ev_cp_permanent_assignment_constraints(self):
        # Constraint: number of EVs sharing one CP
        def num_ev_sharing_cp(model, j):
            return sum(model.is_ev_permanently_assigned_to_cp[i, j] for i in model.EV_ID) <= model.num_ev_per_cp[j]

        self.model.num_ev_sharing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_sharing_cp
        )

        # Constraint: each EV can only be assigned to one CP
        def ev_to_cp_mutual_excl_permanent_assignment(model, i):
            return sum(model.is_ev_permanently_assigned_to_cp[i, j] for j in model.CP_ID) == 1

        self.model.ev_to_cp_mutual_excl_permanent_assignment_constraint = pyo.Constraint(
            self.model.EV_ID, rule=ev_to_cp_mutual_excl_permanent_assignment
        )





    '''
    def new_constraint(self):
        # Link total power per EV:
        def ev_total_power(model, i, t):
            return model.p_ev[i, t] == sum(model.p_ev_cp[i, j, t] for j in model.CP_ID)

        self.model.ev_total_power_constraint = pyo.Constraint(self.model.EV_ID, self.model.TIME, rule=ev_total_power)

        def charging_power_limit_per_cp(model, i, j, t):
            return model.p_ev_cp[i, j, t] <= model.p_cp_rated * model.is_ev_cp_connected[i, j, t]

        self.model.charging_power_limit_per_cp_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=charging_power_limit_per_cp
        )

        def cp_power_limit(model, j, t):
            return sum(model.p_ev_cp[i, j, t] for i in model.EV_ID) <= model.p_cp_rated

        self.model.cp_power_limit_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=cp_power_limit
        )
    '''


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

        def charge_only_on_charging_days(model, i, d, j=None):
            if j is not None:
                # Case: is_ev_cp_connected (with charging point index)
                return (sum(model.is_ev_cp_connected[i, j, t] for t in params.T_d[d])
                        <= len(params.T_d[d]) * model.is_charging_day[i, d])
            else:
                # Case: is_ev_charging (without charging point index)
                return (sum(model.is_ev_charging[i, t] for t in params.T_d[d])
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
        self._charging_power_limit_constraints()

        if self.charging_strategy == ChargingStrategy.FLEXIBLE:
            self._scheduling_constraints()

        if self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self._ev_assignment_and_mutual_exclusivity_constraints_config_2_3()
            self._ev_cp_permanent_assignment_constraints()
            # self.new_constraint()
