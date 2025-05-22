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
        bigM = params.p_cp_rated_max
        def charging_power_limit_config_2_3_upper_bound1(model, i, t):
            return model.p_ev[i, t] <= model.p_cp_rated

        model.charging_power_limit_config_2_3_upper_bound1_constraint = pyo.Constraint(
            model.EV_ID, model.TIME, rule=charging_power_limit_config_2_3_upper_bound1
        )

        def charging_power_limit_config_2_3_upper_bound2(model, i, t):
            return model.p_ev[i, t] <= bigM * sum(
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
        self._charging_power_limit_constraints()

        if self.charging_strategy == ChargingStrategy.FLEXIBLE:
            self._scheduling_constraints()

        if self.config == CPConfig.CONFIG_2 or self.config == CPConfig.CONFIG_3:
            self._ev_assignment_and_mutual_exclusivity_constraints_config_2_3()
