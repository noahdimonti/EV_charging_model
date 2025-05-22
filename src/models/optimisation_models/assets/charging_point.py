import pyomo.environ as pyo
from src.config import params
from src.models.configs import CPConfig


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

        self.model.max_ev_per_cp = pyo.Var(within=pyo.NonNegativeIntegers)
        self.model.min_ev_per_cp = pyo.Var(within=pyo.NonNegativeIntegers)

    def _config3_variables(self):
        self.model.num_ev_per_cp = pyo.Var(self.model.CP_ID, within=pyo.NonNegativeIntegers)
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




        # def p_cp_mutual_excl(model, j, t):
        #     return sum(model.p_ev[i, t] for i in model.EV_ID) <= model.p_cp_rated * sum(
        #         model.ev_is_connected_to_cp_j[i, j, t] for i in model.EV_ID)
        #
        # self.model.p_cp_mutual_excl_const = pyo.Constraint(
        #     self.model.CP_ID, self.model.TIME, rule=p_cp_mutual_excl
        # )
        #
        #
        # def total_power_limit_per_cp(model, j, t):
        #     return sum(
        #         model.p_ev[i, t] * model.ev_is_connected_to_cp_j[i, j, t] for i in model.EV_ID) <= model.p_cp_rated
        #
        # self.model.total_power_limit_per_cp_constraint = pyo.Constraint(
        #     self.model.CP_ID, self.model.TIME, rule=total_power_limit_per_cp
        # )
        #


        # self.model.p_ev_at_cp = pyo.Var(self.model.EV_ID, self.model.CP_ID, self.model.TIME)
        #
        # def link_p_ev_cp(model, i, j, t):
        #     return model.p_ev_at_cp[i, j, t] <= model.p_ev[i, t]
        #
        # self.model.link_p_ev_cp_c = pyo.Constraint(
        #     self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=link_p_ev_cp
        # )
        #
        # def restrict_by_connection(model, i, j, t):
        #     bigM = params.num_of_evs
        #     return model.p_ev_at_cp[i, j, t] <= bigM * model.ev_is_connected_to_cp_j[i, j, t]
        #
        # self.model.restrict_by_connection_c = pyo.Constraint(
        #     self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=restrict_by_connection
        # )
        #
        # def cp_power_limit(model, j, t):
        #     return sum(model.p_ev_at_cp[i, j, t] for i in model.EV_ID) <= model.p_cp_rated * model.cp_is_installed[j]
        #
        # self.model.cp_power_limit_constraint = pyo.Constraint(
        #     self.model.CP_ID, self.model.TIME, rule=cp_power_limit
        # )

        self.model.p_ev_cp = pyo.Var(self.model.EV_ID, self.model.CP_ID, self.model.TIME, within=pyo.NonNegativeReals)

        # Link total power per EV:
        def ev_total_power(model, i, t):
            return model.p_ev[i, t] == sum(model.p_ev_cp[i, j, t] for j in model.CP_ID)

        self.model.ev_total_power_constraint = pyo.Constraint(self.model.EV_ID, self.model.TIME, rule=ev_total_power)

        def charging_power_limit_per_cp(model, i, j, t):
            return model.p_ev_cp[i, j, t] <= model.p_cp_rated * model.ev_is_connected_to_cp_j[i, j, t]

        self.model.charging_power_limit_per_cp_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=charging_power_limit_per_cp
        )

        def cp_power_limit(model, j, t):
            return sum(model.p_ev_cp[i, j, t] for i in model.EV_ID) <= model.p_cp_rated

        self.model.cp_power_limit_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=cp_power_limit
        )

        def ev_to_cp_mutual_exclusivity(model, i, t):
            return sum(model.ev_is_connected_to_cp_j[i, j, t] for j in model.CP_ID) <= 1

        self.model.ev_to_cp_mutual_exclusivity_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.TIME, rule=ev_to_cp_mutual_exclusivity
        )

        def cp_to_ev_mutual_exclusivity(model, j, t):
            return sum(model.ev_is_connected_to_cp_j[i, j, t] for i in model.EV_ID) <= 1

        self.model.cp_to_ev_mutual_exclusivity_constraint = pyo.Constraint(
            self.model.CP_ID, self.model.TIME, rule=cp_to_ev_mutual_exclusivity
        )

    def _ev_cp_permanent_assignment_constraints(self):
        # Constraint: number of EVs sharing one CP
        def num_ev_sharing_cp(model, j):
            return sum(model.ev_is_permanently_assigned_to_cp[i, j] for i in model.EV_ID) <= model.num_ev_per_cp[j]

        self.model.num_ev_sharing_cp_constraint = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_sharing_cp
        )

        # Constraint: each EV can only be assigned to one CP
        def ev_to_cp_mutual_excl_permanent_assignment(model, i):
            return sum(model.ev_is_permanently_assigned_to_cp[i, j] for j in model.CP_ID) == 1

        self.model.ev_to_cp_mutual_excl_permanent_assignment_constraint = pyo.Constraint(
            self.model.EV_ID, rule=ev_to_cp_mutual_excl_permanent_assignment
        )

        # Constraint: EVs can only be connected to its assigned CP
        def ev_cp_connection(model, i, j, t):
            return model.ev_is_connected_to_cp_j[i, j, t] <= model.ev_is_permanently_assigned_to_cp[i, j]

        self.ev_cp_connection_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.CP_ID, self.model.TIME, rule=ev_cp_connection
        )

    def _num_ev_per_cp_limit_constraints(self):
        bigM = params.num_of_evs

        # Constraint: Each CP's EV count must be <= max_ev_per_cp
        def num_ev_per_cp_upper_limit(model, j):
            return model.num_ev_per_cp[j] <= model.max_ev_per_cp + (bigM * (1 - model.cp_is_installed[j]))

        self.model.num_ev_per_cp_upper_limit_constraints = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_per_cp_upper_limit
        )

        # Constraint: Each CP's EV count must be >= min_ev_per_cp
        def num_ev_per_cp_lower_limit(model, j):
            return model.num_ev_per_cp[j] >= model.min_ev_per_cp - (bigM * (1 - model.cp_is_installed[j]))

        self.model.num_ev_per_cp_lower_limit_constraints = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_per_cp_lower_limit
        )

        # No EVs can be assigned to a CP that isn't installed
        def cp_ev_count_zero_if_not_installed(model, j):
            return model.num_ev_per_cp[j] <= bigM * model.cp_is_installed[j]

        self.model.zero_if_not_installed = pyo.Constraint(
            self.model.CP_ID, rule=cp_ev_count_zero_if_not_installed
        )

        # Constraint: The difference between max and min must be at most a certain threshold
        def even_distribution_rule(model):
            return model.max_ev_per_cp - model.min_ev_per_cp <= params.ev_distribution_imbalance_threshold

        self.model.even_distribution_constraint = pyo.Constraint(
            rule=even_distribution_rule
        )

    def _evs_share_installed_cp_constraints(self):
        # Big M linearisation
        def evs_share_installed_cp_upper_bound(model, j):
            return model.num_ev_per_cp[j] <= params.num_of_evs * model.cp_is_installed[j]

        self.model.evs_share_installed_cp_upper_bound_constraint = pyo.Constraint(
            self.model.CP_ID, rule=evs_share_installed_cp_upper_bound
        )

        def total_num_ev_share(model):
            return sum(model.num_ev_per_cp[j] for j in model.CP_ID) == params.num_of_evs

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
