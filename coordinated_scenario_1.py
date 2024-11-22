import pyomo.environ as pyo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pprint import pprint
import params
import create_ev_data
from ModelOutputs import ModelOutputs


# Model brief description
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
Minimise cost
'''

def create_model_instance(tariff_type: str, num_of_evs: int, avg_travel_distance: float, min_soc: float):
    # instantiate EV objects
    EV = create_ev_data.main(num_of_evs, avg_travel_distance, min_soc)

    # create dictionaries of ev parameters, key: ev id, value: the parameter value
    soc_min_dict = {}
    soc_max_dict = {}
    soc_init_dict = {}
    soc_final_dict = {}
    dep_time_dict = {}
    arr_time_dict = {}
    travel_energy_dict = {}
    at_home_status_dict = {}

    for ev_id in range(num_of_evs):
        soc_min_dict[ev_id] = EV[ev_id].soc_min
        soc_max_dict[ev_id] = EV[ev_id].soc_max
        soc_init_dict[ev_id] = EV[ev_id].soc_init
        soc_final_dict[ev_id] = EV[ev_id].soc_final
        at_home_status_dict[ev_id] = EV[ev_id].at_home_status
        dep_time_dict[ev_id] = EV[ev_id].t_dep
        arr_time_dict[ev_id] = EV[ev_id].t_arr

    # create travel energy dict, structure: { (ev_id, dep_time): energy_consumption_value }
    for ev_id in range(num_of_evs):
        for idx, dep_time in enumerate(dep_time_dict[ev_id]):
            # take the value according to dep_time index
            travel_energy_dict[(ev_id, dep_time)] = EV[ev_id].travel_energy[idx]

    # ------------------- model construction ------------------- #

    # instantiate concrete model
    model = pyo.ConcreteModel(name=f'CS1_{tariff_type}_{num_of_evs}EVs_{avg_travel_distance}km_SOCmin{min_soc}')

    # initialise sets
    model.TIME = pyo.Set(initialize=params.timestamps)
    model.EV_ID = pyo.Set(initialize=[i for i in range(num_of_evs)])

    # initialise parameters
    # connection points (CP)
    num_of_cps = num_of_evs  # the num of CP in this model is the same as num of EV, however, it can be different

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
                                       initialize=lambda model, i, t: model.SOC_EV_min[i] +
                                                                      model.travel_energy_consumption[i, t],
                                       within=pyo.NonNegativeReals)

    # costs
    model.tariff = pyo.Param(
        model.TIME, within=pyo.NonNegativeReals, initialize=params.tariff_dict[tariff_type]
    )

    # initialise variables
    model.P_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))
    model.P_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))
    model.SOC_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                           bounds=lambda model, i, t: (model.min_required_SOC[i, t], model.SOC_EV_max[i]))
    model.delta_P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)
    model.P_peak = pyo.Var(within=pyo.NonNegativeReals)

    # P_EV_max optimisation choice (integer)
    model.P_EV_max_selection = pyo.Var(range(len(params.P_EV_max_list)), within=pyo.Binary)
    model.P_EV_max = pyo.Var(within=pyo.NonNegativeReals)
    model.P_EV = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)

    # initialise constraints
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

    # grid constraint
    def grid_constraint(model, t):
        return model.P_grid[t] == model.P_household_load[t] + sum(model.P_EV[i, t] for i in model.EV_ID)

    model.grid_constraint = pyo.Constraint(model.TIME, rule=grid_constraint)

    # P_EV constraint
    def max_available_charging_power(model, t):
        return sum(model.P_EV[i, t] for i in model.EV_ID) <= model.P_cp[t]

    model.max_available_charging_power = pyo.Constraint(model.TIME, rule=max_available_charging_power)

    # charging power constraint for when EV is at home/away
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

    model.charging_power_change_constraint = pyo.Constraint(model.EV_ID, model.TIME,
                                                            rule=charging_power_change_constraint)

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

    # set final soc constraint
    def final_soc_constraint(model, i):
        return model.SOC_EV[i, model.TIME.last()] >= model.SOC_EV_final[i]

    model.final_soc = pyo.Constraint(model.EV_ID, rule=final_soc_constraint)

    # constraint that defines peak power in linear terms
    def peak_power_constraint(model, t):
        return model.P_peak >= sum(model.P_EV[i, t] for i in model.EV_ID) + model.P_household_load[t]

    model.peak_power_constraint = pyo.Constraint(model.TIME, rule=peak_power_constraint)

    # initialise objective function
    def obj_function(model):
        investment_cost = params.investment_cost
        charging_continuity_penalty = params.charging_continuity_penalty

        # investment and maintenance costs
        total_investment_cost = num_of_cps * sum(investment_cost[p] * model.P_EV_max_selection[p]
                                           for p in range(len(params.P_EV_max_list)))
        # per charging point for the duration
        maintenance_cost = params.annual_maintenance_cost / 365 * params.num_of_days * num_of_cps

        # electricity purchase costs
        household_load_cost = sum(model.tariff[t] * model.P_household_load[t] for t in model.TIME)
        ev_charging_cost = sum(model.tariff[t] * model.P_EV[i, t] for i in model.EV_ID for t in model.TIME)
        grid_import_cost = household_load_cost + ev_charging_cost

        # other costs
        daily_supply_charge = params.daily_supply_charge_dict[tariff_type]
        total_charging_continuity_penalty = sum(charging_continuity_penalty * model.delta_P_EV[i, t]
                                          for i in model.EV_ID
                                          for t in model.TIME)

        return (total_investment_cost + maintenance_cost +
                grid_import_cost + daily_supply_charge +
                total_charging_continuity_penalty + model.P_peak)

    model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    return model

