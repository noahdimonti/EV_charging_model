import pyomo.environ as pyo

class BaseModel:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_parameters()
        self.initialise_variables()
        self.define_constraints()

        def initialise_parameters(self):
            pass  # Override in child classes

        def initialise_variables(self):
            pass  # Override in child classes

        def define_constraints(self):
            pass  # Override in child classes

class Grid(BaseModel):
    def initialise_variables(self):
        self.model.p_grid = pyo.Var(self.model.TIME)

