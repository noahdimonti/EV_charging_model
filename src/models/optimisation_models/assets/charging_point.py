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

    def initialise_variables(self):
        # Variables for selecting CP rated power (for all configs)
        self._cp_rated_power_selection_variables()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_variables()

        elif self.config == CPConfig.CONFIG_3:
            self._num_cp_decision_variables()
            self._ev_cp_permanent_assignment_variables()

    def initialise_constraints(self):
        # Constraints for selecting CP rated power (for all configs)
        self._cp_rated_power_selection_constraints()

        if self.config == CPConfig.CONFIG_2:
            self._num_cp_decision_constraints()
            self._total_charging_demand()

        elif self.config == CPConfig.CONFIG_3:
            self._num_cp_decision_constraints()
            self._total_charging_demand()
            self._ev_cp_permanent_assignment_constraints()
            self._evs_share_installed_cp_constraints()
            self._even_distribution_ev_per_cp()

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
        self.model.is_cp_installed = pyo.Var(
            self.model.CP_ID, within=pyo.Binary
        )
        self.model.p_cp_total = pyo.Var(
            within=pyo.NonNegativeReals
        )

    def _ev_cp_permanent_assignment_variables(self):
        self.model.num_ev_per_cp = pyo.Var(self.model.CP_ID, within=pyo.NonNegativeIntegers)
        self.model.is_ev_permanently_assigned_to_cp = pyo.Var(
            self.model.EV_ID, self.model.CP_ID, within=pyo.Binary
        )

        self.model.max_ev_per_cp = pyo.Var(within=pyo.NonNegativeIntegers)
        self.model.min_ev_per_cp = pyo.Var(within=pyo.NonNegativeIntegers)

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

    # CONFIG 2 AND 3 Constraint
    def _num_cp_decision_constraints(self):
        # Constraint: decision for the number of CPs installed
        def cp_count(model):
            return sum(model.is_cp_installed[j] for j in model.CP_ID) == model.num_cp

        self.model.cp_count_constraint = pyo.Constraint(rule=cp_count)

    # CONFIG 2 AND 3 Constraint
    def _total_charging_demand(self):
        # Constraint: ensuring total EV charging demand can be met by the number of installed CPs
        def p_cp_total(model, t):
            return sum(model.p_ev[i, t] for i in model.EV_ID) <= model.num_cp * model.p_cp_rated  # THIS IS THE BILINEAR CONSTRAINT!!!!

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

    # CONFIG 3 Constraint
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

    # CONFIG 3 Constraint
    def _evs_share_installed_cp_constraints(self):
        def evs_share_installed_cp_upper_bound(model, j):
            return model.num_ev_per_cp[j] <= params.num_of_evs * model.is_cp_installed[j]

        self.model.evs_share_installed_cp_upper_bound_constraint = pyo.Constraint(
            self.model.CP_ID, rule=evs_share_installed_cp_upper_bound
        )

        def total_num_ev_share(model):
            return sum(model.num_ev_per_cp[j] for j in model.CP_ID) == params.num_of_evs

        self.model.total_num_ev_share_constraint = pyo.Constraint(rule=total_num_ev_share)

    def _even_distribution_ev_per_cp(self):
        bigM = params.num_of_evs

        # Constraint: Each CP's EV count must be <= max_ev_per_cp
        def num_ev_per_cp_upper_limit(model, j):
            return model.num_ev_per_cp[j] <= model.max_ev_per_cp + (bigM * (1 - model.is_cp_installed[j]))

        self.model.num_ev_per_cp_upper_limit_constraints = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_per_cp_upper_limit
        )

        # Constraint: Each CP's EV count must be >= min_ev_per_cp
        def num_ev_per_cp_lower_limit(model, j):
            return model.num_ev_per_cp[j] >= model.min_ev_per_cp - (bigM * (1 - model.is_cp_installed[j]))

        self.model.num_ev_per_cp_lower_limit_constraints = pyo.Constraint(
            self.model.CP_ID, rule=num_ev_per_cp_lower_limit
        )

        # No EVs can be assigned to a CP that isn't installed
        def cp_ev_count_zero_if_not_installed(model, j):
            return model.num_ev_per_cp[j] <= bigM * model.is_cp_installed[j]

        self.model.zero_if_not_installed = pyo.Constraint(
            self.model.CP_ID, rule=cp_ev_count_zero_if_not_installed
        )

        # Constraint: The difference between max and min must be at most a certain threshold
        def even_distribution_rule(model):
            return model.max_ev_per_cp - model.min_ev_per_cp <= params.ev_distribution_imbalance_threshold

        self.model.even_distribution_constraint = pyo.Constraint(
            rule=even_distribution_rule
        )
