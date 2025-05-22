import pyomo.environ as pyo


class CommonConnectionPoint:
    def __init__(self, model):
        self.model = model

    def initialise_constraints(self):
        def energy_balance_rule(model, t):
            return model.p_grid[t] == model.p_household_load[t] + sum(model.p_ev[i, t] for i in model.EV_ID)

        self.model.ccp_constraint = pyo.Constraint(self.model.TIME, rule=energy_balance_rule)
