import pyomo.environ as pyo
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from src.config import params
from pprint import pprint
from src.utils import solve_model
import itertools
from src.config.ev_params import (
    soc_init_dict,
    soc_critical_dict,
    soc_max_dict,
    at_home_status_dict,
    t_arr_dict,
    t_dep_dict,
    travel_energy_dict
)


def main():
    model = create_optimisation_model_instance()
    solve_model.solve_optimisation_model(model)

    # model_data.p_grid.display()
    # model_data.p_household_load.display()
    # model_data.p_cp.display()
    # model_data.p_ev.display()
    # model_data.soc_ev.display()
    #
    # model_data.p_daily_peak.display()
    # model_data.p_daily_avg.display()
    # model_data.delta_daily_peak_avg.display()

    print(pyo.value(model.p_cp_max))



def create_optimisation_model_instance():
    # instantiate concrete model_data
    model = pyo.ConcreteModel(name='config_1')

    tariff_type = 'flat'

    # ---------------------------------
    # SETS (done)
    # ---------------------------------
    model.TIME = pyo.Set(initialize=params.timestamps)
    model.EV_ID = pyo.Set(initialize=[_ for _ in range(params.num_of_evs)])

    model.CP_ID = pyo.Set(initialize=[_ for _ in range(params.num_of_evs)])  # if this is config_1

    model.DAY = pyo.Set(initialize=[_ for _ in params.T_d.keys()])
    model.WEEK = pyo.Set(initialize=[_ for _ in params.D_w.keys()])

    # ---------------------------------
    # PARAMETERS
    # ---------------------------------

    # household load (done)
    household_load_path = f'../../data/interim/load_profile_{params.num_of_days}_days_{params.num_of_households}_households.csv'
    household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)
    model.p_household_load = pyo.Param(model.TIME, initialize=household_load)

    # EV (done)
    model.soc_critical = pyo.Param(model.EV_ID, initialize=soc_critical_dict)
    model.soc_max = pyo.Param(model.EV_ID, initialize=soc_max_dict)
    model.soc_init = pyo.Param(model.EV_ID, initialize=soc_init_dict)

    model.ev_at_home_status = pyo.Param(model.EV_ID, model.TIME,
                                        initialize=lambda model, i, t: at_home_status_dict[i].loc[t, f'EV_ID{i}'],
                                        within=pyo.Binary)

    # costs
    model.tariff = pyo.Param(
        model.TIME, within=pyo.NonNegativeReals, initialize=params.tariff_dict[tariff_type]
    )

    # ---------------------------------
    # VARIABLES (done)
    # ---------------------------------

    # Grid (done)
    model.p_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))
    model.p_peak = pyo.Var(model.DAY, within=pyo.NonNegativeReals)
    model.p_avg = pyo.Var(model.DAY, within=pyo.NonNegativeReals)
    model.delta_peak_avg = pyo.Var(model.DAY, within=pyo.NonNegativeReals)

    # CP (done)
    model.p_cp = pyo.Var(model.CP_ID, model.TIME, within=pyo.NonNegativeReals)

    # CP rated power selection variables (done)
    model.select_cp_rated_power = pyo.Var(params.p_cp_rated_options_scaled, within=pyo.Binary)
    model.p_cp_max = pyo.Var(within=pyo.NonNegativeReals)

    # EV (done)
    model.p_ev = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)
    model.soc_ev = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                           bounds=lambda model, i, t: (0, model.soc_max[i]))



    # ---------------------------------
    # CONSTRAINTS
    # ---------------------------------

    # Grid - daily peak power constraints (done)
    model.peak_power_constraint = pyo.ConstraintList()

    for d in model.DAY:
        for t in params.T_d[d]:
            model.peak_power_constraint.add(model.p_peak[d] >= model.p_grid[t])

    def peak_average(model, d):
        return model.p_daily_avg[d] == (1 / len(params.T_d[d])) * sum(model.p_grid[t] for t in params.T_d[d])

    model.peak_average_constraint = pyo.Constraint(
        model.DAY, rule=peak_average
    )

    model.delta_peak_average_constraint = pyo.ConstraintList()

    for d in model.DAY:
        model.delta_peak_average_constraint.add(model.delta_peak_avg[d] >= (model.p_peak[d] - model.p_avg[d]))
        model.delta_peak_average_constraint.add(model.delta_peak_avg[d] >= (model.p_avg[d] - model.p_peak[d]))



    # CCP constraint (done)
    def energy_balance_rule(model, t):
        return model.p_grid[t] == model.p_household_load[t] + sum(model.p_cp[j, t] for j in model.CP_ID)

    model.ccp_constraint = pyo.Constraint(model.TIME, rule=energy_balance_rule)


    # CP constraints (done)
    # Constraint to select optimal rated power of the charging points
    def rated_power_selection(model):
        return model.p_cp_rated == sum(
            model.select_cp_rated_power[j] * j for j in params.p_cp_rated_options_scaled
        )

    model.rated_power_selection_constraint = pyo.Constraint(rule=rated_power_selection)

    # Constraint to ensure only one rated power variable is selected
    def mutual_exclusivity_rated_power_selection(model):
        return sum(model.select_cp_rated_power[j] for j in params.p_cp_rated_options_scaled) == 1

    model.mutual_exclusivity_rated_power_selection_constraint = pyo.Constraint(
        rule=mutual_exclusivity_rated_power_selection
    )

    # CP power limits
    model.cp_power_limits_constraint = pyo.ConstraintList()

    for j in model.CP_ID:
        for t in model.TIME:
            model.cp_power_limits_constraint.add(model.p_cp[j, t] >= 0)
            model.cp_power_limits_constraint.add(model.p_cp[j, t] <= model.p_cp_max)


    # CP-EV relationship
    # def cp_ev_relationship(model_data, i, j, t):
    #     return model_data.p_ev[i, t] == model_data.p_cp[j, t]
    #
    # model_data.cp_ev_relationship_constraint = pyo.Constraint(
    #     model_data.EV_ID, model_data.CP_ID, model_data.TIME, rule=cp_ev_relationship
    # )


    # EV Constraints (done)
    # EV charging power constraints
    model.ev_charging_power_limits_constraint = pyo.ConstraintList()

    for i in model.EV_ID:
        for t in model.TIME:
            model.ev_charging_power_limits_constraint.add(
                model.p_ev[i, t] >= 0
            )
            model.ev_charging_power_limits_constraint.add(
                model.p_ev[i, t] <= model.ev_at_home_status[i, t] * model.p_cp_max
            )


    # SOC Constraints (done)

    def get_trip_number_k(i, t):
        if t in t_arr_dict[i]:
            k = t_arr_dict[i].index(t)
        elif t in t_dep_dict[i]:
            k = t_dep_dict[i].index(t)
        else:
            return None
        return k

    model.soc_limits_constraint = pyo.ConstraintList()

    for i in model.EV_ID:
        for t in model.TIME:
            model.soc_limits_constraint.add(model.soc_ev[i, t] <= model.soc_max[i])
            model.soc_limits_constraint.add(model.soc_ev[i, t] >= model.soc_critical[i])

    def soc_evolution(model, i, t):
        # set initial soc
        if t == model.TIME.first():
            return model.soc_ev[i, t] == model.soc_init[i]

        # constraint to set ev soc at arrival time
        elif t in t_arr_dict[i]:
            k = get_trip_number_k(i, t)
            return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] - travel_energy_dict[i][k]

        # otherwise soc follows regular charging constraint
        else:
            return model.soc_ev[i, t] == model.soc_ev[i, model.TIME.prev(t)] + (
                    params.charging_efficiency * model.p_ev[i, t])

    model.soc_evolution = pyo.Constraint(model.EV_ID, model.TIME, rule=soc_evolution)

    def minimum_required_soc_at_departure(model, i, t):
        # SOC required before departure time
        if t in t_dep_dict[i]:
            k = get_trip_number_k(i, t)
            return model.soc_ev[i, t] >= model.soc_critical[i] + travel_energy_dict[i][k]
        return pyo.Constraint.Skip

    model.minimum_required_soc_at_departure_constraint = pyo.Constraint(
        model.EV_ID, model.TIME, rule=minimum_required_soc_at_departure
    )

    def final_soc_rule(model, i):
        return model.soc_ev[i, model.TIME.last()] >= model.soc_init[i]

    model.final_soc_constraint = pyo.Constraint(model.EV_ID, rule=final_soc_rule)




    # ------------------------------------
    # OBJECTIVE FUNCTION
    # ------------------------------------

    def get_economic_cost(model):
        # investment cost
        investment_cost = len(model.CP_ID) * sum(params.investment_cost[j] * model.select_cp_rated_power[j]
                                                 for j in params.p_cp_rated_options_scaled)

        # maintenance cost per charging point for the duration
        maintenance_cost = (params.annual_maintenance_cost / 365) * params.num_of_days * len(model.CP_ID)

        # operational cost
        operational_cost = params.daily_supply_charge_dict[tariff_type]

        # electricity purchase cost
        energy_purchase_cost = sum(params.tariff_dict[tariff_type][t] * model.p_grid[t] for t in model.TIME)

        # total costs
        total_economic_cost = investment_cost + maintenance_cost + operational_cost + energy_purchase_cost

        return total_economic_cost

    def get_load_cost(model):
        return sum(model.delta_daily_peak_avg[d] for d in model.DAY)

    def get_soc_cost(model):
        return sum(model.soc_max[i] - model.soc_ev[i, t] for i in model.EV_ID for t in t_dep_dict[i])

    w_cost = 0.5
    w_load = 0.25
    w_soc = 0.25

    def obj_function(model):
        economic_cost = get_economic_cost(model)
        load_cost = get_load_cost(model)
        soc_cost = get_soc_cost(model)

        return (w_cost * economic_cost) + (w_load * load_cost) + (w_soc * soc_cost)

    model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    return model


if __name__ == '__main__':
    main()
