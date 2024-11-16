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

# create dictionaries of ev parameters, key: ev id, value: the parameter value
soc_min_dict = {}
soc_max_dict = {}
soc_init_dict = {}
soc_final_dict = {}
dep_time_dict = {}
arr_time_dict = {}
travel_energy_dict = {}
at_home_status_dict = {}

for ev_id in range(params.num_of_evs):
    soc_min_dict[ev_id] = EV[ev_id].soc_min
    soc_max_dict[ev_id] = EV[ev_id].soc_max
    soc_init_dict[ev_id] = EV[ev_id].soc_init
    soc_final_dict[ev_id] = EV[ev_id].soc_final
    at_home_status_dict[ev_id] = EV[ev_id].at_home_status
    dep_time_dict[ev_id] = EV[ev_id].t_dep
    arr_time_dict[ev_id] = EV[ev_id].t_arr

# create travel energy dict, structure: { (ev_id, dep_time): energy_consumption_value }
for ev_id in range(params.num_of_evs):
    for idx, dep_time in enumerate(dep_time_dict[ev_id]):
        travel_energy_dict[(ev_id, dep_time)] = EV[ev_id].travel_energy[idx]  # take the value according to dep_time idx

for i in range(params.num_of_evs):
    print(EV[i].soc_min, EV[i].soc_max, EV[i].soc_init, EV[i].travel_energy)


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
#     print(model.P_household_load[t])

# EV
model.P_EV_min = pyo.Param(initialize=0)
model.P_EV_max = pyo.Param(initialize=params.P_EV_max)

model.SOC_EV_min = pyo.Param(model.EV_ID, initialize=soc_min_dict)
model.SOC_EV_max = pyo.Param(model.EV_ID, initialize=soc_max_dict)
model.SOC_EV_init = pyo.Param(model.EV_ID, initialize=soc_init_dict)
model.SOC_EV_final = pyo.Param(model.EV_ID, initialize=soc_final_dict)

model.EV_at_home_status = pyo.Param(model.EV_ID, model.TIME,
                                    initialize=lambda model, i, t: at_home_status_dict[i].loc[t, f'EV_ID{i}'],
                                    within=pyo.Binary)

model.travel_energy_consumption = pyo.Param(model.EV_ID, model.TIME,
                                            initialize=lambda model, i, t: travel_energy_dict.get((i, t), 0),
                                            within=pyo.NonNegativeReals)

model.min_required_SOC = pyo.Param(model.EV_ID, model.TIME,
                                   initialize=lambda model, i, t: model.SOC_EV_min[i] + model.travel_energy_consumption[
                                       i, t],
                                   within=pyo.NonNegativeReals)

# cost
model.energy_cost = pyo.Param(initialize=params.energy_cost)  # cost ($/kW)
model.grid_operational_cost = pyo.Param(initialize=params.grid_operational_cost)


# initialise variables
model.P_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.P_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals, bounds=(0, model.P_EV_max))

model.SOC_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                       bounds=lambda model, i, t: (model.min_required_SOC[i, t], model.SOC_EV_max[i]))


# constraints
def cp_constraint(model, t):
    return model.P_cp[t] <= model.P_grid[t] - model.P_household_load[t]

model.cp_constraint = pyo.Constraint(model.TIME, rule=cp_constraint)


# P_EV constraint
def max_available_charging_power(model, t):
    return sum(model.P_EV[i, t] for i in model.EV_ID) <= model.P_cp[t]

model.max_available_charging_power = pyo.Constraint(model.TIME, rule=max_available_charging_power)


def charging_power_constraint(model, i, t):
    # set P_EV to zero if ev is away
    if model.EV_at_home_status[i, t] == 0:
        return model.P_EV[i, t] == 0
    # otherwise P_EV is less than or equal to maximum
    else:
        return model.P_EV[i, t] <= model.P_EV_max

model.charging_power_constraint = pyo.Constraint(model.EV_ID, model.TIME, rule=charging_power_constraint)


# SOC constraints
def get_departure_time(ev_id, arrival_time):
    # Get the list of departure times for this EV from the departure_dict
    dep_times = dep_time_dict[ev_id]

    # Find the latest departure time that occurs before the arrival time
    valid_dep_times = [dep_time for dep_time in dep_times if dep_time < arrival_time]

    # Return the latest departure time if it exists, otherwise return None
    if valid_dep_times:
        return max(valid_dep_times)
    else:
        return None  # No valid departure time before arrival_time


def soc_evolution(model, i, t):
    # set initial soc
    if t == model.TIME.first():
        return model.SOC_EV[i, t] == model.SOC_EV_init[i]

    # constraint to set ev soc at arrival time
    elif t in arr_time_dict[i]:
        dep_time = get_departure_time(i, t)
        return model.SOC_EV[i, t] == model.SOC_EV[i, dep_time] - model.travel_energy_consumption[i, dep_time]

    # otherwise soc follows regular charging constraint
    else:
        previous_time = model.TIME.prev(t)
        return model.SOC_EV[i, t] == model.SOC_EV[i, previous_time] + model.P_EV[i, t]


model.soc_evolution = pyo.Constraint(model.EV_ID, model.TIME, rule=soc_evolution)


def final_soc_constraint(model, i):
    return model.SOC_EV[i, model.TIME.last()] >= model.SOC_EV_final[i]

model.final_soc = pyo.Constraint(model.EV_ID, rule=final_soc_constraint)


# objective function
def obj_function(model):
    return sum(model.energy_cost * model.P_EV[i, t] +
               model.grid_operational_cost * model.P_grid[t]
               for i in model.EV_ID for t in model.TIME)

model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)


# solve the model
solver = pyo.SolverFactory('gurobi')
solver.solve(model, tee=True)
# model.display()
# model.P_cp.display()
# model.P_grid.display()

# model.SOC_EV.display()
# model.P_EV.display()

p_ev_dict = {}
for i in model.EV_ID:
    p_ev_dict[i] = []
    for t in model.TIME:
        p_ev_dict[i].append(pyo.value(model.P_EV[i, t]))

df = pd.DataFrame(p_ev_dict, index=model.TIME)
df['ev_load'] = df.sum(axis=1)
df['cp'] = [pyo.value(model.P_cp[t]) for t in model.TIME]
df['household_load'] = household_load['household_load']
df['total_load'] = df['household_load'] + df['ev_load']
print(df)
print(f'EV load: {df.ev_load.max()}')
print(f'CP load: {df.cp.max()}')

peak_total = []
for day in set(household_load.index.day):
    daily_peak = household_load.loc[(household_load.index.day == day), 'household_load'].max()
    peak_total.append(daily_peak)

avg_daily_peak = sum(peak_total) / len(peak_total)
print(avg_daily_peak)


fig = go.Figure()
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.household_load, name='Household Load'))
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.ev_load, name='EV Load'))
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.total_load, name='Total Load'))
fig.add_trace(
    go.Scatter(x=[t for t in model.TIME], y=[avg_daily_peak for i in range(len(model.TIME))], name='Average daily peak'))
fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Coordinated Scenario',
                  xaxis_title='Timestamp',
                  yaxis_title='Load (kW)')
fig.show()



def plot(ev_id):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=timestamps, y=[pyo.value(model.SOC_EV[ev_id, t]) for t in model.TIME],
                             name='SOC'))
    fig.add_trace(go.Scatter(x=timestamps, y=[pyo.value(model.P_EV[ev_id, t]) for t in model.TIME],
                             name='Charging Power'))

    fig.update_layout(title=f'SOC and Charging Power of EV_ID{ev_id} - Coordinated Scenario',
                      xaxis_title='Timestamp')
    fig.show()

# for i in range(params.num_of_evs):
#     plot(i)