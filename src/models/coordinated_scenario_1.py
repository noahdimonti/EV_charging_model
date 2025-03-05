import pyomo.environ as pyo
import pickle
import pandas as pd
from src.config import params
from pprint import pprint
from src.utils import solve_model
import itertools

def main():
    mdl = create_optimisation_model_instance()
    solve_model.solve_optimisation_model(mdl)
    mdl.soc_ev.display()
    # mdl.p_ev.display()
    # mdl.p_grid.display()
    mdl.p_peak.display()
    mdl.p_avg.display()
    mdl.delta_peak_avg.display()

    print(pyo.value(mdl.P_EV_max))


def create_optimisation_model_instance():
    # Load EV data
    filename = f'../../data/processed/EV_instances_{params.num_of_evs}'
    with open(filename, "rb") as f:
        ev_instance_list = pickle.load(f)

    # ------------------- model construction ------------------- #

    # instantiate concrete model
    model = pyo.ConcreteModel(name='config_1')

    tariff_type = 'flat'

    # Initialise data
    soc_init_dict = {ev.ev_id: ev.soc_init for ev in ev_instance_list}
    soc_critical_dict = {ev.ev_id: ev.soc_critical for ev in ev_instance_list}
    soc_max_dict = {ev.ev_id: ev.soc_max for ev in ev_instance_list}

    at_home_status_dict = {ev.ev_id: ev.at_home_status for ev in ev_instance_list}
    t_arr_dict = {ev.ev_id: ev.t_arr for ev in ev_instance_list}
    t_dep_dict = {ev.ev_id: ev.t_dep for ev in ev_instance_list}
    travel_energy_dict = {ev.ev_id: ev.travel_energy for ev in ev_instance_list}

    # ---------------------------------
    # SETS
    # ---------------------------------
    model.TIME = pyo.Set(initialize=params.timestamps)
    model.EV_ID = pyo.Set(initialize=[i for i in range(params.num_of_evs)])

    model.DAY = pyo.Set(initialize=[i for i in params.T_d.keys()])
    model.WEEK = pyo.Set(initialize=[i for i in params.D_w.keys()])

    # ---------------------------------
    # PARAMETERS
    # ---------------------------------
    # connection points (CP)
    model.num_of_cps = pyo.Param(initialize=params.num_of_evs)

    # household load
    household_load_path = f'../../data/interim/load_profile_{params.num_of_days}_days_{params.num_of_households}_households.csv'
    household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)
    model.p_household_load = pyo.Param(model.TIME, initialize=household_load)

    # EV
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
    # VARIABLES
    # ---------------------------------
    model.p_grid = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))
    model.p_cp = pyo.Var(model.TIME, within=pyo.NonNegativeReals, bounds=(0, params.P_grid_max))

    # P_EV_max optimisation choice (integer)
    model.P_EV_max_selection = pyo.Var(params.P_EV_max_list, within=pyo.Binary)
    model.P_EV_max = pyo.Var(within=pyo.NonNegativeReals)

    model.soc_ev = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals,
                           bounds=lambda model, i, t: (0, model.soc_max[i]))
    model.p_ev = pyo.Var(model.EV_ID, model.TIME, within=pyo.NonNegativeReals)

    model.p_peak = pyo.Var(model.DAY, within=pyo.NonNegativeReals)
    model.p_avg = pyo.Var(model.DAY, within=pyo.NonNegativeReals)
    model.delta_peak_avg = pyo.Var(model.DAY, within=pyo.NonNegativeReals)

    # ---------------------------------
    # CONSTRAINTS
    # ---------------------------------

    # constraint to define P_EV_max
    def P_EV_max_selection_rule(model):
        return model.P_EV_max == sum(
            model.P_EV_max_selection[j] * j for j in params.P_EV_max_list
        )

    model.P_EV_max_selection_rule = pyo.Constraint(rule=P_EV_max_selection_rule)

    # constraint to ensure only one P_EV_max variable is selected
    def mutual_exclusivity_rule(model):
        return sum(model.P_EV_max_selection[j] for j in params.P_EV_max_list) == 1

    model.mutual_exclusivity_rule = pyo.Constraint(rule=mutual_exclusivity_rule)

    # grid constraint
    def grid_constraint(model, t):
        return model.p_grid[t] == model.p_household_load[t] + sum(model.p_ev[i, t] for i in model.EV_ID)

    model.grid_constraint = pyo.Constraint(model.TIME, rule=grid_constraint)

    # charging power constraint for when EV is at home/away
    def charging_power_when_disconnected(model, i, t):
        # set P_EV to zero if ev is away
        if model.ev_at_home_status[i, t] == 0:
            return model.p_ev[i, t] == 0

        return pyo.Constraint.Skip

    model.charging_power_when_disconnected = pyo.Constraint(
        model.EV_ID, model.TIME, rule=charging_power_when_disconnected
    )

    def charging_power_limit(model, i, t):
        return model.p_ev[i, t] <= model.P_EV_max

    model.charging_power_limit = pyo.Constraint(model.EV_ID, model.TIME, rule=charging_power_limit)

    # Daily peak power constraints
    model.peak_power_constraint = pyo.ConstraintList()

    for d in model.DAY:
        for t in params.T_d[d]:
            model.peak_power_constraint.add(model.p_peak[d] >= model.p_grid[t])

    def peak_average(model, d):
        return model.p_avg[d] == (1 / len(params.T_d[d])) * sum(model.p_grid[t] for t in params.T_d[d])

    model.peak_average_constraint = pyo.Constraint(
        model.DAY, rule=peak_average
    )

    model.delta_peak_average_constraint = pyo.ConstraintList()

    for d in model.DAY:
        model.delta_peak_average_constraint.add(model.delta_peak_avg[d] >= (model.p_peak[d] - model.p_avg[d]))
        model.delta_peak_average_constraint.add(model.delta_peak_avg[d] >= (model.p_avg[d] - model.p_peak[d]))

    # ------------------------------------
    # SOC Constraints
    # ------------------------------------

    def get_trip_number_k(i, t):
        if t in t_arr_dict[i]:
            k = t_arr_dict[i].index(t)
        elif t in t_dep_dict[i]:
            k = t_dep_dict[i].index(t)
        else:
            return None
        return k

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

    model.minimum_required_soc_at_departure = pyo.Constraint(
        model.EV_ID, model.TIME, rule=minimum_required_soc_at_departure
    )

    # set final soc constraint
    def final_soc_constraint(model, i):
        return model.soc_ev[i, model.TIME.last()] >= model.soc_init[i]

    model.final_soc = pyo.Constraint(model.EV_ID, rule=final_soc_constraint)

    # ------------------------------------
    # OBJECTIVE FUNCTION
    # ------------------------------------

    def get_economic_cost(model):
        # investment and maintenance costs
        investment_cost = model.num_of_cps * sum(params.investment_cost[j] * model.P_EV_max_selection[j]
                                                 for j in params.P_EV_max_list)
        # per charging point for the duration
        maintenance_cost = params.annual_maintenance_cost / 365 * params.num_of_days * model.num_of_cps

        # operational costs
        operational_cost = params.daily_supply_charge_dict[tariff_type]

        # electricity purchase costs
        household_load_cost = sum(model.tariff[t] * model.p_household_load[t] for t in model.TIME)
        ev_charging_cost = sum(model.tariff[t] * model.p_ev[i, t] for i in model.EV_ID for t in model.TIME)

        total_economic_cost = investment_cost + maintenance_cost + household_load_cost + ev_charging_cost + operational_cost

        return total_economic_cost

    def get_load_cost(model):
        return sum(model.delta_peak_avg[d] for d in model.DAY)

    def get_soc_cost(model):
        return sum(model.soc_max[i] - model.soc_ev[i, t] for i in model.EV_ID for t in t_dep_dict[i])

    w_cost = 0.5
    w_load = 0.5
    w_soc = 0

    def obj_function(model):
        economic_cost = get_economic_cost(model)
        load_cost = get_load_cost(model)
        soc_cost = get_soc_cost(model)

        return (w_cost * economic_cost) + (w_load * load_cost) + (w_soc * soc_cost)

    model.obj_function = pyo.Objective(rule=obj_function, sense=pyo.minimize)

    return model


if __name__ == '__main__':
    main()
