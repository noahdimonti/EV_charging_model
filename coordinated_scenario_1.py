import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        # take the value according to dep_time index
        travel_energy_dict[(ev_id, dep_time)] = EV[ev_id].travel_energy[idx]


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
# model.P_EV_max = pyo.Param(initialize=params.P_EV_max)

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
model.grid_operational_cost = pyo.Param(initialize=params.grid_operational_cost)
model.flat_tariff = pyo.Param(model.TIME, initialize=params.energy_cost_flat_tariff)
model.tou_tariff = pyo.Param(model.TIME, initialize=params.tou_tariff)

# expression for tariff variations
model.ev_charging_cost = pyo.Expression(expr=0)


# initialise variables
model.P_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.P_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

# model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals, bounds=(0, model.P_EV_max))

model.SOC_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                       bounds=lambda model, i, t: (model.min_required_SOC[i, t], model.SOC_EV_max[i]))

model.delta_P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)


# P_EV_max optimisation choice (integer)
model.P_EV_max_choice = pyo.Var(range(len(params.P_EV_max_list)), within=pyo.Binary)
model.P_EV_max = pyo.Var(within=pyo.NonNegativeReals)
model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)


def P_EV_max_selection_rule(model):
    return model.P_EV_max == sum(
        model.P_EV_max_choice[j] * params.P_EV_max_list[j] for j in range(len(params.P_EV_max_list))
    )

model.P_EV_max_selection = pyo.Constraint(rule=P_EV_max_selection_rule)


def P_EV_max_choice_constraint(model):
    return sum(model.P_EV_max_choice[j] for j in range(len(params.P_EV_max_list))) == 1

model.P_EV_max_choice_constraint = pyo.Constraint(rule=P_EV_max_choice_constraint)


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


# constraint for delta_P_EV to penalise frequent on/off charging
def charging_power_change_constraint(model, i, t):
    if t == model.TIME.first():
        return model.delta_P_EV[i, t] == 0
    else:
        previous_time = model.TIME.prev(t)
        return model.delta_P_EV[i, t] >= model.P_EV[i, t] - model.P_EV[i, previous_time]

model.charging_power_change_constraint = pyo.Constraint(model.EV_ID, model.TIME, rule=charging_power_change_constraint)


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


# set ev charging cost options
def set_ev_charging_cost(model, tariff_type):

    if tariff_type == 'flat_tariff':
        model.ev_charging_cost = pyo.Expression(
            expr=sum(model.flat_tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)
        )

    elif tariff_type == 'tou_tariff':
        model.ev_charging_cost = pyo.Expression(
            expr=sum(model.tou_tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)
        )

    elif tariff_type != 'flat_tariff' & tariff_type != 'tou_tariff':
        raise ValueError("Invalid tariff_type. Use 'flat_tariff' or 'tou_tariff'.")


# objective function
def obj_function(model):
    # ev_charging_cost = sum(model.flat_tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)
    # ev_charging_cost = sum(model.tou_tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)

    grid_operational_cost = sum(model.grid_operational_cost * model.P_grid[t] for t in model.TIME)
    continuity_penalty = sum(0.1 * model.delta_P_EV[i, t] for i in model.EV_ID for t in model.TIME)

    return model.ev_charging_cost + grid_operational_cost + continuity_penalty

model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)


# run model for different tariffs
tariff_types = ['flat_tariff', 'tou_tariff']

# create dictionary of values for each model
results = {}

for tariff in tariff_types:
    # Set the EV charging cost based on the tariff
    set_ev_charging_cost(model, tariff)


    # solve the model
    solver = pyo.SolverFactory('gurobi')
    solver.solve(model, tee=True)
    # model.display()
    # model.P_cp.display()
    # model.P_grid.display()

    # model.SOC_EV.display()
    # model.P_EV.display()

    results[tariff] = {
        'P_EV_max': f'{pyo.value(model.P_EV_max)} kW',
        'Optimal value': f'${pyo.value(model.obj_function)}'
    }

    # print(f'Tariff type: {tariff}')
    # print(f'\nObjective function: ${pyo.value(model.obj_function)}')
    # print(f'\nP_EV_max: {pyo.value(model.P_EV_max)} kW')

pprint(results)

# results visualisation
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
print(f'avg daily peak: {avg_daily_peak}')


# flat tariff plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.household_load, name='Household Load'))
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.ev_load, name='EV Load'))
fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.total_load, name='Total Load'))
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=[avg_daily_peak for i in range(len(model.TIME))],
                         name='Average daily peak'))

fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Coordinated Scenario',
                  xaxis_title='Timestamp',
                  yaxis_title='Load (kW)')
# fig.show()




# ToU tariff plot
# Create figure with secondary y-axis
fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.household_load,
                         name='Household Load'),
                         secondary_y=False)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.ev_load,
                         name='EV Load'),
                         secondary_y=False)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=df.total_load,
                         name='Total Load'),
                         secondary_y=False)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=[avg_daily_peak for i in range(len(model.TIME))],
                         name='Average daily peak'),
                         secondary_y=False)
fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                         y=[i for i in params.tou_tariff['tariff']],
                         name='ToU tariff'),
                         secondary_y=True)

fig.update_layout(title=f'Load Profile (85 Households and {params.num_of_evs} EVs) - Coordinated Scenario')

# Set x-axis title
fig.update_xaxes(title_text='Timestamp')

# Set y-axes titles
fig.update_yaxes(title_text='Tariff ($/kW)', secondary_y=False)
fig.update_yaxes(title_text='Load (kW)', secondary_y=True)

# fig.show()



def plot_each_ev(ev_id):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=timestamps, y=[pyo.value(model.SOC_EV[ev_id, t]) for t in model.TIME],
                             name='SOC'))
    fig.add_trace(go.Scatter(x=timestamps, y=[pyo.value(model.P_EV[ev_id, t]) for t in model.TIME],
                             name='Charging Power'))

    fig.update_layout(title=f'SOC and Charging Power of EV_ID{ev_id} - Coordinated Scenario',
                      xaxis_title='Timestamp')
    fig.show()

# for i in range(params.num_of_evs):
#     plot_each_ev(i)