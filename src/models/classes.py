import pyomo.environ as pyo
import pandas as pd
from src.config import params as prm
from src.config import ev_params as ev_prm
import pickle
from pprint import pprint
from src.utils import solve_model


def main():
    # Create the optimization model
    ev_model = EVChargingModel(prm, ev_prm)
    model = ev_model.get_model()

    evcharge = EVChargingScheduling(model, ev_prm)
    print(evcharge.__dict__)

    # Solve model
    # solve_model.solve_optimisation_model(model)
    # model.display()


class Grid:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_variables()

    def initialise_variables(self):
        # Grid import power
        self.model.p_grid = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals, bounds=(0, self.params.P_grid_max))

        # Peak and average power
        self.model.p_peak = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.p_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)
        self.model.delta_peak_avg = pyo.Var(self.model.DAY, within=pyo.NonNegativeReals)

    def initialise_constraints(self):
        self.model.peak_power_constraint = pyo.ConstraintList()

        for d in self.model.DAY:
            for t in self.params.T_d[d]:
                self.model.peak_power_constraint.add(self.model.p_peak[d] >= self.model.p_grid[t])

        def peak_average(model, d):
            return model.p_avg[d] == (1 / len(self.params.T_d[d])) * sum(model.p_grid[t] for t in self.params.T_d[d])

        self.model.peak_average_constraint = pyo.Constraint(
            self.model.DAY, rule=peak_average
        )

        self.model.delta_peak_average_constraint = pyo.ConstraintList()

        for d in self.model.DAY:
            self.model.delta_peak_average_constraint.add(self.model.delta_peak_avg[d] >= (self.model.p_peak[d] - self.model.p_avg[d]))
            self.model.delta_peak_average_constraint.add(self.model.delta_peak_avg[d] >= (self.model.p_avg[d] - self.model.p_peak[d]))


class HouseholdLoad:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_parameters()

    def initialise_parameters(self):
        household_load_path = f'../../data/interim/load_profile_{self.params.num_of_days}_days_{self.params.num_of_households}_households.csv'
        household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)
        self.model.p_household_load = pyo.Param(self.model.TIME, initialize=household_load)


class CommonConnectionPoint:
    def __init__(self, model, params):
        self.model = model
        self.params = params

    def initialise_constraints(self):
        def energy_balance_rule(model, t):
            return model.p_grid[t] == model.p_household_load[t] + sum(model.p_ev[i, t] for i in model.EV_ID)

        self.model.ccp_constraint = pyo.Constraint(self.model.TIME, rule=energy_balance_rule)


class ChargingPoint:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_variables()

    def initialise_variables(self):
        self.model.p_cp = pyo.Var(self.model.TIME, within=pyo.NonNegativeReals)

    def initialise_constraints(self):
        pass


class ElectricVehicle:
    def __init__(self, model, params):
        self.model = model
        self.params = params
        self.initialise_parameters()
        self.initialise_variables()

    def initialise_parameters(self):
        self.model.soc_critical = pyo.Param(self.model.EV_ID, initialize=self.params.soc_critical_dict)
        self.model.soc_max = pyo.Param(self.model.EV_ID, initialize=self.params.soc_max_dict)
        self.model.soc_init = pyo.Param(self.model.EV_ID, initialize=self.params.soc_init_dict)

        self.model.ev_at_home_status = pyo.Param(self.model.EV_ID, self.model.TIME,
                                                 initialize=lambda model, i, t:
                                                 self.params.at_home_status_dict[i].loc[t, f'EV_ID{i}'],
                                                 within=pyo.Binary)

    def initialise_variables(self):
        self.model.p_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals)
        self.model.soc_ev = pyo.Var(self.model.EV_ID, self.model.TIME, within=pyo.NonNegativeReals,
                                    bounds=lambda model, i, t: (0, model.soc_max[i]))

    def initialise_constraints(self):
        def get_trip_number_k(i, t):
            if t in self.params.t_arr_dict[i]:
                k = self.params.t_arr_dict[i].index(t)
            elif t in self.params.t_dep_dict[i]:
                k = self.params.t_dep_dict[i].index(t)
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
            elif t in self.params.t_arr_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] - self.params.travel_energy_dict[i][k]

            # otherwise soc follows regular charging constraint
            else:
                return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] + (
                        self.params.charging_efficiency * model.p_ev[i, t])

        self.model.soc_evolution = pyo.Constraint(self.model.EV_ID, self.model.TIME, rule=soc_evolution)

        def minimum_required_soc_at_departure(model, i, t):
            # SOC required before departure time
            if t in self.params.t_dep_dict[i]:
                k = get_trip_number_k(i, t)
                return model.soc_ev[i, t] >= model.soc_critical[i] + self.params.travel_energy_dict[i][k]
            return pyo.Constraint.Skip

        self.model.minimum_required_soc_at_departure_constraint = pyo.Constraint(
            self.model.EV_ID, self.model.TIME, rule=minimum_required_soc_at_departure
        )

        def final_soc_rule(model, i):
            return model.soc_ev[i, model.TIME.last()] >= model.soc_init[i]

        self.model.final_soc_constraint = pyo.Constraint(self.model.EV_ID, rule=final_soc_rule)


class EVChargingScheduling(ElectricVehicle):
    def __init__(self, model, params):
        self.model = model
        self.params = params
        super().__init__(self.model, self.params)





class EVChargingModel:
    def __init__(self, global_constants, ev_params):
        self.global_constants = global_constants
        self.ev_params = ev_params
        self.model = pyo.ConcreteModel()
        self.assets = {}
        self.initialise_sets()
        self.assemble_components()
        self.define_objective()

    def initialise_sets(self):
        self.model.TIME = pyo.Set(initialize=self.global_constants.timestamps)
        self.model.EV_ID = pyo.Set(initialize=[i for i in range(self.global_constants.num_of_evs)])
        self.model.DAY = pyo.Set(initialize=[i for i in self.global_constants.T_d.keys()])
        self.model.WEEK = pyo.Set(initialize=[i for i in self.global_constants.D_w.keys()])

    def assemble_components(self):
        # Initialise assets parameters and variables
        self.assets['grid'] = Grid(self.model, self.global_constants)
        self.assets['household'] = HouseholdLoad(self.model, self.global_constants)
        self.assets['ccp'] = CommonConnectionPoint(self.model, self.global_constants)
        self.assets['ev'] = ElectricVehicle(self.model, self.ev_params)

        self.assets['ccp'].initialise_constraints()
        self.assets['ev'].initialise_constraints()

    def define_objective(self):
        def objective_function(model):
            return sum(model.p_grid[t] for t in model.TIME)

        self.model.obj_function = pyo.Objective(rule=objective_function, sense=pyo.minimize)

    def get_model(self):
        return self.model


if __name__ == "__main__":
    main()
