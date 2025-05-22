import pyomo.environ as pyo
from src.config import params


class Grid:
    def __init__(self, model):
        self.model = model
        self.initialise_variables()

    def initialise_variables(self):
        # Grid import power
        self.model.p_grid = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))
