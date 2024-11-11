import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from pprint import pprint
import params

# initiate EV parameters
exec(open('params.py').read())

'''
Nodes and constraints:
- Household load -> param (P_household_load_t)
- Grid -> variable (P_grid_t), params (P_grid_min=0, P_grid_max)
- CP -> variable P_CP_t = P_grid_t - P_household_load_t
- EV -> var (P_EV_i_t), params (P_EV_i_min, P_EV_i_max)
        sum(P_EV_i_t) <= P_CP_t
        0 <= P_EV_i_t <= P_EV_i_max
        var (SOC_EV_i_t), params (SOC_EV_i_min, SOC_EV_i_max)
        SOC constraints ...


Objective:
There's a cost associated with every kW of P_EV. Minimise this cost.
obj = sum( cost * P_EV_i_t ), for all i and t
'''

# instantiate EV objects
EV = params.EV

# create a list of ev soc min and max
evs_soc_min = {}
evs_soc_max = {}
evs_soc_init = {}
evs_soc_t_arr = {}
evs_at_home_status = {}
for ev_id in range(params.num_of_evs):
    evs_soc_min[ev_id] = EV[ev_id].soc_min
    evs_soc_max[ev_id] = EV[ev_id].soc_max
    evs_soc_init[ev_id] = EV[ev_id].soc_init
    evs_soc_t_arr[ev_id] = EV[ev_id].soc_t_arr
    evs_at_home_status[ev_id] = EV[ev_id].at_home_status

print(evs_soc_t_arr)
# instantiate concrete model
model = pyo.ConcreteModel()

# initialise sets
timestamps = pd.date_range(start=params.start_date_time,
                           periods=params.periods_in_a_day * params.num_of_days,
                           freq=f'{params.time_resolution}min')
model.TIME = pyo.Set(initialize=timestamps)
model.EV_ID = pyo.Set(initialize=[i for i in range(params.num_of_evs)])


# initialise parameters
# household load
household_load = pd.read_csv(filepath_or_buffer='load_profile_7_days_85_households.csv', parse_dates=True, index_col=0)
model.P_household_load = pyo.Param(model.TIME, initialize=household_load)

# for t in model.TIME:
#     print(f'Load: {model.P_household_load[t]}')

# EV
model.P_EV_min = pyo.Param(initialize=0)
model.P_EV_max = pyo.Param(initialize=params.P_EV_max)

model.SOC_EV_min = pyo.Param(model.EV_ID, initialize=evs_soc_min)
model.SOC_EV_max = pyo.Param(model.EV_ID, initialize=evs_soc_max)
model.SOC_EV_init = pyo.Param(model.EV_ID, initialize=evs_soc_init)


def soc_t_arr_init(model, i, t):
    if t in evs_soc_t_arr.get(i, {}):
        return evs_soc_t_arr[i][t]
    else:
        return None

model.SOC_EV_t_arr = pyo.Param(model.EV_ID, model.TIME,
                               initialize=soc_t_arr_init, within=pyo.Any)

model.EV_at_home_status = pyo.Param(model.EV_ID, model.TIME,
                                    initialize=lambda model, i, t: evs_at_home_status[i].loc[t, f'EV_ID{i}'])


# for i in model.EV_ID:
#     for t in model.TIME:
#         print(f'EV {i}, Time {t}: {model.EV_at_home_status[i,t]}')

# for i in model.EV_ID:
#     for t in model.TIME:
#         print(f'EV {i}, Time {t}: {model.SOC_EV_t_arr[i,t]}')


# cost
model.cost = pyo.Param(initialize=params.energy_cost)  # cost ($/kW)


# initialise variables
model.P_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.P_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals)

model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_EV_max))
model.SOC_EV = pyo.Var(model.EV_ID, model.TIME, bounds=lambda model, i, t: (model.SOC_EV_min[i], model.SOC_EV_max[i]))



# constraints
# CP constraint: P_CP_t = P_grid_t - P_household_load_t
def cp_constraint(model, t):
    return model.P_cp[t] == model.P_grid[t] - model.P_household_load[t]

model.ccp_constraint = pyo.Constraint(model.TIME, rule=cp_constraint)


# P_EV constraint
def max_available_charging_power(model, t):
    return sum(model.P_EV[i, t] for i in model.EV_ID) <= model.P_cp[t]

model.max_available_charging_power = pyo.Constraint(model.TIME, rule=max_available_charging_power)


def charging_power_constraint(model, i, t):
    if model.EV_at_home_status[i, t] == 0:
        return model.P_EV[i, t] == 0
    else:
        return model.P_EV[i, t] <= model.P_EV_max

model.charging_power_constraint = pyo.Constraint(model.EV_ID, model.TIME, rule=charging_power_constraint)



# SOC constraints
def soc_constaint(model, i, t):
    if t == model.TIME.first():
        return model.SOC_EV[i, t] == model.SOC_EV_init[i]
    else:
        previous_time = model.TIME.prev(t)
        return model.SOC_EV[i, t] == model.SOC_EV[i, previous_time] + model.P_EV[i, t]

model.soc_constraint = pyo.Constraint(model.EV_ID, model.TIME, rule=soc_constaint)

def soc_t_arr_constraint(model, i, t): 
    if model.SOC_EV_t_arr[i, t] is not None:
        previous_time = model.TIME.prev(t)
        return model.SOC_EV[i, t] == model.SOC_EV[i, previous_time] + model.P_EV[i, t] - model.SOC_EV_t_arr[i, t]
    else:
        return pyo.Constraint.Skip

model.soc_t_arr_constraint = pyo.Constraint(model.EV_ID, model.TIME, rule=soc_t_arr_constraint)



# objective function
def obj_function(model):
    return sum(model.cost * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)

model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)


# solve the model
solver = pyo.SolverFactory('gurobi')
solver.solve(model, tee=True)
model.display()

# results = solver.solve(model, tee=True)
# print(f"Solver status: {results.solver.status}")
# if results.solver.status == pyo.SolverStatus.error:
#     print(f"Solver error: {results.solver.termination_condition}")
