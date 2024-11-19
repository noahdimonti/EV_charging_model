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
model.TIME = pyo.Set(initialize=params.timestamps)
model.EV_ID = pyo.Set(initialize=[i for i in range(params.num_of_evs)])
# model.DAYS = pyo.Set(initialize=sorted(list(set(timestamps.day))))

# initialise parameters
# household load
model.P_household_load = pyo.Param(model.TIME, initialize=params.household_load)

# EV
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

# costs
model.tariff = pyo.Param(model.TIME, initialize=params.tariff)

# initialise variables
model.P_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.P_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

model.SOC_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                       bounds=lambda model, i, t: (model.min_required_SOC[i, t], model.SOC_EV_max[i]))

model.delta_P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)

# model.daily_peak_power = pyo.Var(model.DAYS, within=pyo.NonNegativeReals)

# P_EV_max optimisation choice (integer)
model.P_EV_max_selection = pyo.Var(range(len(params.P_EV_max_list)), within=pyo.Binary)
model.P_EV_max = pyo.Var(within=pyo.NonNegativeReals)
model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)


# constraint to define P_EV_max
def P_EV_max_selection_rule(model):
    return model.P_EV_max == sum(
        model.P_EV_max_selection[j] * params.P_EV_max_list[j] for j in range(len(params.P_EV_max_list))
    )

model.P_EV_max_selection_rule = pyo.Constraint(rule=P_EV_max_selection_rule)


# constraint to ensure only one P_EV_max variable is selected
def mutual_exclusivity_rule(model):
    return sum(model.P_EV_max_selection[j] for j in range(len(params.P_EV_max_list))) == 1

model.mutual_exclusivity_rule = pyo.Constraint(rule=mutual_exclusivity_rule)


# CP constraint
def cp_constraint(model, t):
    return model.P_cp[t] == model.P_grid[t] - model.P_household_load[t]

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


# def daily_peak_power_constraint(model, d, t):
#     # Ensure that the daily peak power is greater than or equal to the total power at each timestamp
#     if t.date() == d:  # Only enforce this for timestamps in the same day
#         return model.daily_peak_power[d] >= sum(model.P_EV[i, t] for i in model.EV_ID) + model.P_household_load[t]
#     return pyo.Constraint.Skip  # Skip for timestamps not in day `d`
#
# model.daily_peak_power_constraint = pyo.Constraint(model.DAYS, model.TIME, rule=daily_peak_power_constraint)
#
# model.avg_daily_peak_power = pyo.Expression(expr=sum(model.daily_peak_power[d] for d in model.DAYS) / len(model.DAYS))


# objective function
def obj_function(model):
    investment_cost = params.num_of_evs * sum(params.investment_cost[p] * model.P_EV_max_selection[p]
                                              for p in range(len(params.P_EV_max_list)))
    grid_operational_cost = sum(params.grid_operational_cost * model.P_grid[t] for t in model.TIME)
    maintenance_cost = params.maintenance_cost

    ev_charging_cost = sum(model.tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)
    daily_supply_charge = params.daily_supply_charge

    continuity_penalty = sum(params.charging_continuity_penalty * model.delta_P_EV[i, t]
                             for i in model.EV_ID
                             for t in model.TIME)

    return (investment_cost + grid_operational_cost + maintenance_cost +
            ev_charging_cost + daily_supply_charge + continuity_penalty)

model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)


# solve the model
solver = pyo.SolverFactory('gurobi')
solver.solve(model, tee=True)

# print(f'Avg daily peak power: {pyo.value(model.avg_daily_peak_power)}')

# results data collection
model.P_grid.display()
def print_results():
    p_ev_dict = {}
    for i in model.EV_ID:
        p_ev_dict[f'EV_ID{i}'] = []
        for t in model.TIME:
            p_ev_dict[f'EV_ID{i}'].append(pyo.value(model.P_EV[i, t]))

    df = pd.DataFrame(p_ev_dict, index=[t for t in model.TIME])
    df['ev_load'] = df.sum(axis=1)
    df['cp'] = [pyo.value(model.P_cp[t]) for t in model.TIME]
    df['grid'] = [pyo.value(model.P_grid[t]) for t in model.TIME]
    df['household_load'] = params.household_load['household_load']
    df['total_load'] = df['household_load'] + df['ev_load']
    print(df)

    print(f'Number of households: {params.num_of_households}')
    print(f'Number of EVs: {params.num_of_evs}')

    print(f'\nTariff type: {params.tariff_type}')
    print(f'P_EV_max: {pyo.value(model.P_EV_max * params.P_EV_resolution_factor)} kW')

    print(f'Optimal total cost: ${pyo.value(model.obj_function)}')

    investment_cost = params.num_of_evs * sum(params.investment_cost[p] * pyo.value(model.P_EV_max_selection[p])
                                              for p in range(len(params.P_EV_max_list)))
    grid_operational_cost = sum(params.grid_operational_cost * pyo.value(model.P_grid[t]) for t in model.TIME)
    maintenance_cost = params.maintenance_cost

    ev_charging_cost = sum(model.tariff[t] * pyo.value(model.P_EV[i, t]) for i in model.EV_ID for t in model.TIME)
    daily_supply_charge = params.daily_supply_charge

    continuity_penalty = sum(params.charging_continuity_penalty * pyo.value(model.delta_P_EV[i, t])
                             for i in model.EV_ID
                             for t in model.TIME)
    print(f'Investment cost: ${investment_cost}')
    print(f'Grid operational cost: ${grid_operational_cost}')
    print(f'Maintenance cost: ${maintenance_cost}')
    print(f'Total EV charging cost: ${ev_charging_cost}')
    print(f'Daily supply charge: ${daily_supply_charge}')
    print(f'Continuity penalty cost: ${continuity_penalty}')

    print(f'Peak EV load: {df.ev_load.max()}')
    print(f'Peak total load: {df.total_load.max()}')
    print(f'Peak grid import: {df.grid.max()}')

    peak_total = []
    for day in set(df.index.day):
        daily_peak = df.loc[(df.index.day == day), 'total_load'].max()
        peak_total.append(daily_peak)

    avg_daily_peak = sum(peak_total) / len(peak_total)
    print(f'Average daily peak: {avg_daily_peak}')

    peak_to_average = df['total_load'].max() / df['total_load'].mean()
    print(f'Peak to average ratio: {peak_to_average}')

print_results()

# ------------------- results visualisation ------------------- #

def visualise_results():
    # flat tariff plot
    flat_tariff_fig = go.Figure()
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.household_load, name='Household Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.ev_load, name='EV Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME], y=df.total_load, name='Total Load'))
    flat_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                         y=[avg_daily_peak for i in range(len(model.TIME))],
                                         name='Average daily peak'))

    flat_tariff_fig.update_layout(
        title=f'Load Profile ({params.num_of_households} Households and {params.num_of_evs} EVs) - '
              f'Coordinated Scenario - {params.tariff_type.title()} Tariff',
        xaxis_title='Timestamp',
        yaxis_title='Load (kW)')

    # ToU tariff plot
    # Create figure with secondary y-axis
    # tou_tariff_fig = make_subplots(specs=[[{"secondary_y": True}]])
    tou_tariff_fig = make_subplots(rows=2, cols=1,
                                   subplot_titles=(
                                       f'Load Profile ({params.num_of_households} Households and {params.num_of_evs} EVs) - '
                                       f'Coordinated Scenario - {params.tariff_type.title()} Tariff', 'Price Signal'))

    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.household_load,
                                        name='Household Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.ev_load,
                                        name='EV Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=df.total_load,
                                        name='Total Load'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=[avg_daily_peak for i in range(len(model.TIME))],
                                        name='Average daily peak'),
                             # secondary_y=False,
                             row=1, col=1)
    tou_tariff_fig.add_trace(go.Scatter(x=[t for t in model.TIME],
                                        y=[i for i in params.tou_tariff['tariff']],
                                        name='ToU tariff'),
                             # secondary_y=True,
                             row=2, col=1)

    tou_tariff_fig.update_layout(xaxis2_title='Timestamp',
                                 yaxis1_title='Load (kW)',
                                 yaxis2_title='Price ($/kW)')


    # tou_tariff_fig.update_layout(
    #     title=f'Load Profile ({params.num_of_households} Households and {params.num_of_evs} EVs) - '
    #           f'Coordinated Scenario - {params.tariff_type.title()} Tariff')

    # Set x-axis title
    # tou_tariff_fig.update_xaxes(title_text='Timestamp')

    # Set y-axes titles
    # tou_tariff_fig.update_yaxes(title_text='Tariff ($/kW)', secondary_y=True)
    # tou_tariff_fig.update_yaxes(title_text='Load (kW)', secondary_y=False)


    def plot_results():
        if params.tariff_type == 'flat':
            flat_tariff_fig.show()
        elif params.tariff_type == 'tou':
            tou_tariff_fig.show()


    # plot_results()


    def plot_each_ev(ev_id):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=params.timestamps, y=[pyo.value(model.SOC_EV[ev_id, t]) for t in model.TIME],
                                 name='SOC'))
        fig.add_trace(go.Scatter(x=params.timestamps, y=[pyo.value(model.P_EV[ev_id, t]) for t in model.TIME],
                                 name='Charging Power'))

        fig.update_layout(title=f'SOC and Charging Power of EV_ID{ev_id} - Coordinated Scenario',
                          xaxis_title='Timestamp')
        fig.show()

    # for i in range(params.num_of_evs):
    #     plot_each_ev(i)
