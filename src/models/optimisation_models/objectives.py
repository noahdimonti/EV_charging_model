import pyomo.environ as pyo
from src.config import params, ev_params, independent_variables


class EconomicObjective:
    def __init__(self, model):
        self.model = model

    def investment_cost(self):
        return self.model.num_cp * sum(params.investment_cost[m] * self.model.select_cp_rated_power[m]
                                       for m in params.p_cp_rated_options_scaled)

    def maintenance_cost(self):
        return (params.annual_maintenance_cost / 365) * params.num_of_days * self.model.num_cp

    def energy_purchase_cost(self):
        operational_cost = params.daily_supply_charge_dict[
                               independent_variables.tariff_type] * params.num_of_evs * params.num_of_days

        energy_purchase_cost = sum(
            params.tariff_dict[independent_variables.tariff_type][t] * self.model.p_grid[t] for t in self.model.TIME
        )

        return operational_cost + energy_purchase_cost


class TechnicalObjective:
    def __init__(self, model):
        self.model = model

    def f_papr(self):
        # Initialise variables
        # Daily peak and average power
        self.model.p_daily_peak = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.p_daily_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.delta_daily_peak_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)

        # Weekly peak and average power
        self.model.p_weekly_peak = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        self.model.p_weekly_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)
        self.model.delta_weekly_peak_avg = pyo.Var(self.model.WEEK, within=pyo.NonNegativeReals)

        # Initialise constraints
        # Daily constraints
        self._add_peak_constraints(
            peak_var=self.model.p_daily_peak,
            avg_var=self.model.p_daily_avg,
            delta_var=self.model.delta_daily_peak_avg,
            time_sets=params.T_d,
            index_set=self.model.DAY,
            name_prefix='daily'
        )

        # Weekly constraints
        self._add_peak_constraints(
            peak_var=self.model.p_weekly_peak,
            avg_var=self.model.p_weekly_avg,
            delta_var=self.model.delta_weekly_peak_avg,
            time_sets=params.T_w,
            index_set=self.model.WEEK,
            name_prefix='weekly'
        )

        # Define objective
        daily_load_variance = sum(self.model.delta_daily_peak_avg[d] for d in self.model.DAY)
        weekly_load_variance = sum(self.model.delta_weekly_peak_avg[w] for w in self.model.WEEK)

        return daily_load_variance + weekly_load_variance

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

    def f_peak(self):
        # Initialise parameters
        self.model.high_load_penalty = pyo.Param(self.model.TIME,
                                                 initialize=lambda model, t: (self.model.p_household_load[t] / max(
                                                     [self.model.p_household_load[t]])))
        # Define constraints
        high_load_penalty = sum(
            self.model.high_load_penalty[t] * self.model.p_ev[i, t] for i in self.model.EV_ID for t in self.model.TIME)

        return high_load_penalty

    def f_disc(self):
        # Initialise variables
        self.model.delta_p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)

        # Initialise constraints
        self._charging_discontinuity_constraints()

        # Define objective
        charging_discontinuity = sum(
            self.model.delta_p_ev[i, t] for i in self.model.EV_ID for t in self.model.TIME
        )

        return charging_discontinuity

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


class SocialObjective:
    def __init__(self, model):
        self.model = model

    def f_soc(self):
        soc_max_deviation = sum(
            self.model.soc_max[i] - self.model.soc_ev[i, t] for i in self.model.EV_ID for t in ev_params.t_dep_dict[i])

        return soc_max_deviation

    def f_fair(self):
        # Initialise variables
        self.model.soc_avg_deviation = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)
        self.model.daily_soc_avg_t_dep = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)

        def daily_soc_avg_t_dep_rule(model, d):
            n = len(ev_params.t_dep_on_day[d])
            return model.daily_soc_avg_t_dep[d] == (1 / n) * sum(
                model.soc_ev[i, t] for (i, t) in ev_params.t_dep_on_day[d]
            )

        self.model.daily_soc_avg_t_dep_constraint = pyo.Constraint(self.model.DAY, rule=daily_soc_avg_t_dep_rule)

        self.model.soc_avg_deviation_constraints = pyo.ConstraintList()

        for d in ev_params.t_dep_on_day:
            for (i, t) in ev_params.t_dep_on_day[d]:
                self.model.soc_avg_deviation_constraints.add(
                    self.model.soc_avg_deviation[i, t] >= self.model.soc_ev[i, t] - self.model.daily_soc_avg_t_dep[d]
                )
                self.model.soc_avg_deviation_constraints.add(
                    self.model.soc_avg_deviation[i, t] >= self.model.daily_soc_avg_t_dep[d] - self.model.soc_ev[i, t]
                )

        # Initialise constraints
        # def soc_average(model, t):
        #     return model.soc_avg[t] == (1 / params.num_of_evs) * sum(model.soc_ev[i, t] for i in self.model.EV_ID)
        #
        # self.model.soc_average_constraint = pyo.Constraint(
        #     self.model.TIME, rule=soc_average
        # )
        #
        # self.model.soc_avg_deviation_constraints = pyo.ConstraintList()
        #
        # for i in self.model.EV_ID:
        #     for t in self.model.TIME:
        #         self.model.soc_avg_deviation_constraints.add(
        #             self.model.soc_avg_deviation[i, t] >= self.model.soc_ev[i, t] - self.model.soc_avg[t]
        #         )
        #         self.model.soc_avg_deviation_constraints.add(
        #             self.model.soc_avg_deviation[i, t] >= self.model.soc_avg[t] - self.model.soc_ev[i, t]
        #         )

        # Define objective
        soc_avg_deviation = sum(self.model.soc_avg_deviation[i, t] for i in self.model.EV_ID for t in self.model.TIME)

        return soc_avg_deviation
