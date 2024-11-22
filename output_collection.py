import pandas as pd
import pyomo.environ as pyo
from ModelOutputs import ModelOutputs
import params


def collect_model_outputs(model, tariff_type, num_of_evs, avg_travel_distance, min_soc):
    """
    Collects and calculates outputs for a single model simulation.

    Args:
        model: The optimization model object.
        tariff_type: The tariff type used in the simulation ('flat' or 'tou').
        num_of_evs: Number of EVs in the simulation.
        avg_travel_distance: Average travel distance per EV (km).
        min_soc: Minimum state of charge for EVs.

    Returns:
        List of ModelOutputs objects containing metrics for the model.
    """
    # Create a ModelOutputs instance
    model_outputs = ModelOutputs(
        model_name=model.name,
        tariff_type=tariff_type,
        num_of_evs=num_of_evs,
        avg_travel_distance=avg_travel_distance,
        min_soc=min_soc,
    )

    # Calculate cost metrics
    _calculate_cost_metrics(model, model_outputs, tariff_type, num_of_evs)

    # Calculate power metrics
    _calculate_power_metrics(model, model_outputs)

    return model_outputs


def _calculate_cost_metrics(model, model_outputs, tariff_type, num_of_evs):
    """
    Calculates cost-related metrics for the model and updates the ModelOutputs instance.
    """
    model_outputs.total_optimal_cost = pyo.value(model.obj_function)

    # Set number of CPs and households
    model_outputs.num_of_cps = num_of_evs
    model_outputs.num_of_households = params.num_of_households

    # Investment and maintenance costs
    investment_cost = model_outputs.num_of_cps * sum(
        params.investment_cost[p] * pyo.value(model.P_EV_max_selection[p])
        for p in range(len(params.P_EV_max_list))
    )
    maintenance_cost = params.annual_maintenance_cost / 365 * params.num_of_days * model_outputs.num_of_cps
    model_outputs.investment_maintenance_cost = investment_cost + maintenance_cost

    # Household load and EV charging costs
    model_outputs.household_load_cost = sum(
        model.tariff[t] * pyo.value(model.P_household_load[t]) for t in model.TIME
    )
    model_outputs.ev_charging_cost = sum(
        model.tariff[t] * pyo.value(model.P_EV[i, t]) for i in model.EV_ID for t in model.TIME
    )
    model_outputs.grid_import_cost = (
            model_outputs.household_load_cost + model_outputs.ev_charging_cost
    )

    # Other costs (daily supply charge + continuity penalty)
    daily_supply_charge = params.daily_supply_charge_dict[tariff_type]
    continuity_penalty = sum(
        params.charging_continuity_penalty * pyo.value(model.delta_P_EV[i, t])
        for i in model.EV_ID for t in model.TIME
    )
    model_outputs.other_costs = daily_supply_charge + continuity_penalty

    # Calculate average EV charging cost
    model_outputs.calculate_average_ev_charging_cost()


def _calculate_power_metrics(model, model_outputs):
    """
    Calculates power-related metrics for the model and updates the ModelOutputs instance.
    """
    # Load profiles for EVs, households, grid, and total load
    load_profiles = _create_load_profiles(model)
    model_outputs.max_charging_power = pyo.value(model.P_EV_max * params.P_EV_resolution_factor)
    model_outputs.peak_ev_load = load_profiles['ev_load'].max()
    model_outputs.peak_total_demand = load_profiles['total_load'].max()
    model_outputs.peak_grid_import = load_profiles['grid'].max()

    # Calculate average daily peak power
    daily_peaks = load_profiles.resample('D').max()['total_load']
    model_outputs.avg_daily_peak = daily_peaks.mean()

    # Peak-to-average power ratio
    model_outputs.peak_to_average = (
            load_profiles['total_load'].max() / load_profiles['total_load'].mean()
    )


def _create_load_profiles(model):
    """
    Creates load profiles (EV load, household load, grid load, total load) for the model.

    Returns:
        A DataFrame containing load profiles indexed by time.
    """
    # Collect EV power consumption data
    p_ev_dict = {
        f'EV_ID{i}': [pyo.value(model.P_EV[i, t]) for t in model.TIME] for i in model.EV_ID
    }
    df = pd.DataFrame(p_ev_dict, index=[t for t in model.TIME])

    # Aggregate EV load and combine with other loads
    df['ev_load'] = df.sum(axis=1)
    df['grid'] = [pyo.value(model.P_grid[t]) for t in model.TIME]
    df['household_load'] = params.household_load['household_load']
    df['total_load'] = df['household_load'] + df['ev_load']

    return df

