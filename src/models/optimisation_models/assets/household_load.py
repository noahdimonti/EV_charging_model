import pyomo.environ as pyo
from src.config import params


class HouseholdLoad:
    def __init__(self, model):
        self.model = model

        # Initialise parameter
        self.model.p_household_load = pyo.Param(self.model.TIME, initialize=params.household_load)
