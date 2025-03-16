import pandas as pd
import pyomo.environ as pyo

from src.config import params
from src.old_code.model_outputs import ModelOutputs


def collect_model_outputs(model, model_type, tariff_type, num_of_evs, avg_travel_distance, min_soc):
    """
    Collects and calculates outputs for a single model_data simulation.

    Args:
        model: The optimization model_data object.
        model_type: The type of model_data ('uncoordinated' or 'coordinated')
        tariff_type: The tariff type used in the simulation ('flat' or 'tou').
        num_of_evs: Number of EVs in the simulation.
        avg_travel_distance: Average travel distance per EV (km).
        min_soc: Minimum state of charge for EVs.

    Returns:
        List of ModelOutputs objects containing metrics for the model_data.
    """
    # Create a ModelOutputs instance
    model_outputs = ModelOutputs(
        model_name=model.name,
        tariff_type=tariff_type,
        num_of_evs=num_of_evs,
        avg_travel_distance=avg_travel_distance,
        min_soc=min_soc,
    )

    if model_type == 'uncoordinated':
        # Calculate cost metrics
        _calculate_cost_metrics_uncoordinated_model(model, model_outputs, tariff_type)

        # Calculate power metrics
        _calculate_power_metrics_uncoordinated_model(model, model_outputs)

    elif model_type == 'coordinated':
        # Calculate cost metrics
        _calculate_cost_metrics_coordinated_model(model, model_outputs, tariff_type)

        # Calculate power metrics
        _calculate_power_metrics_coordinated_model(model, model_outputs)

    elif model_type != 'uncoordinated' or model_type != 'coordinated':
        raise ValueError('Model type must be either "uncoordinated" or "coordinated".')

    return model_outputs


def _calculate_cost_metrics_coordinated_model(model, model_outputs, tariff_type):
    """
    Calculates cost-related metrics for the model_data and updates the ModelOutputs instance.
    """
    model_outputs.total_cost = pyo.value(model.obj_function)

    # Set number of CPs and households
    model_outputs.num_of_cps = pyo.value(model.num_of_cps)
    model_outputs.num_of_households = params.num_of_households

    # Investment and maintenance costs
    investment_cost = model_outputs.num_of_cps * sum(
        params.investment_cost[p] * pyo.value(model.select_cp_rated_power[p])
        for p in params.p_cp_rated_options_scaled
    )
    maintenance_cost = params.annual_maintenance_cost / 365 * params.num_of_days * model_outputs.num_of_cps
    model_outputs.investment_maintenance_cost = investment_cost + maintenance_cost

    # Household load and EV charging costs
    model_outputs.household_load_cost = sum(
        model.tariff[t] * pyo.value(model.p_household_load[t]) for t in model.TIME
    )
    model_outputs.ev_charging_cost = sum(
        model.tariff[t] * pyo.value(model.p_ev[i, t]) for i in model.EV_ID for t in model.TIME
    )
    model_outputs.grid_import_cost = (
            model_outputs.household_load_cost + model_outputs.ev_charging_cost
    )

    # Other costs (daily supply charge + continuity penalty)
    daily_supply_charge = params.daily_supply_charge_dict[tariff_type]
    discontinuity_penalty = sum(
        params.charging_discontinuity_penalty * pyo.value(model.delta_P_EV[i, t])
        for i in model.EV_ID for t in model.TIME
    )
    peak_penalty = params.peak_penalty * pyo.value(model.p_daily_peak)

    model_outputs.other_costs = daily_supply_charge + discontinuity_penalty + peak_penalty

    # Calculate average EV charging cost
    model_outputs.calculate_average_ev_charging_cost()


def _calculate_power_metrics_coordinated_model(model, model_outputs):
    """
    Calculates power-related metrics for the model_data and updates the ModelOutputs instance.
    """
    # Load profiles for EVs, households, grid, and total load
    load_profiles = _create_load_profiles(model)
    model_outputs.max_charging_power = pyo.value(model.p_cp_rated) * params.charging_power_resolution_factor
    model_outputs.total_ev_load = load_profiles['ev_load'].sum()
    model_outputs.peak_ev_load = load_profiles['ev_load'].max()
    model_outputs.peak_total_demand = load_profiles['total_load'].max()
    model_outputs.peak_grid_import = load_profiles['grid'].max()
    model_outputs.ev_load = load_profiles['ev_load']
    model_outputs.n_connected_ev = model.EV_at_home_status

    # Calculate average daily peak power
    daily_peaks = load_profiles.resample('D').max()['total_load']
    model_outputs.avg_daily_peak = daily_peaks.mean()

    # Peak-to-average power ratio
    model_outputs.peak_to_average = (
            load_profiles['total_load'].max() / load_profiles['total_load'].mean()
    )


def _create_load_profiles(model):
    """
    Creates load profiles (EV load, household load, grid load, total load) for the model_data.

    Returns:
        A DataFrame containing load profiles indexed by time.
    """
    # Collect EV power consumption data_processing
    p_ev_dict = {
        f'EV_ID{i}': [pyo.value(model.p_ev[i, t]) for t in model.TIME] for i in model.EV_ID
    }
    df = pd.DataFrame(p_ev_dict, index=[t for t in model.TIME])

    # Aggregate EV load and combine with other loads
    df['ev_load'] = df.sum(axis=1)
    df['household_load'] = params.household_load['household_load']
    df['grid'] = [pyo.value(model.p_grid[t]) for t in model.TIME]
    df['total_load'] = df['household_load'] + df['ev_load']

    return df


def _calculate_cost_metrics_uncoordinated_model(model, model_outputs, tariff_type):
    """
    Calculates cost-related metrics for the model_data and updates the ModelOutputs instance.
    """
    # Set number of CPs and households
    model_outputs.num_of_cps = model.num_of_cps
    model_outputs.num_of_households = params.num_of_households

    # Investment and maintenance costs
    investment_cost = model_outputs.num_of_cps * params.investment_cost[model.p_ev_max / params.charging_power_resolution_factor]
    maintenance_cost = params.annual_maintenance_cost / 365 * params.num_of_days * model_outputs.num_of_cps
    model_outputs.investment_maintenance_cost = investment_cost + maintenance_cost

    # Household load and EV charging costs
    model_outputs.household_load_cost = (model.household_load * params.tariff_dict[tariff_type]).sum()
    model_outputs.ev_charging_cost = (model.ev_load * params.tariff_dict[tariff_type]).sum()
    model_outputs.grid_import_cost = model_outputs.household_load_cost + model_outputs.ev_charging_cost

    # Other costs (daily supply charge)
    daily_supply_charge = params.daily_supply_charge_dict[tariff_type]
    model_outputs.other_costs = daily_supply_charge

    # Total cost: investment, maintenance, energy purchase, daily supply charge
    model_outputs.total_cost = investment_cost + maintenance_cost + model_outputs.grid_import_cost + daily_supply_charge

    # Calculate average EV charging cost
    model_outputs.calculate_average_ev_charging_cost()


def _calculate_power_metrics_uncoordinated_model(model, model_outputs):
    """
    Calculates power-related metrics for the model_data and updates the ModelOutputs instance.
    """
    # Load profiles for EVs, households, grid, and total load
    model_outputs.max_charging_power = model.p_ev_max
    model_outputs.total_ev_load = model.ev_load.sum()
    model_outputs.peak_ev_load = model.ev_load.max()
    model_outputs.peak_total_demand = model.total_load.max()
    model_outputs.peak_grid_import = model.grid.max()
    model_outputs.ev_load = model.ev_load
    model_outputs.n_connected_ev = model.at_home_status

    # Calculate average daily peak power
    daily_peaks = model.total_load.resample('D').max()
    model_outputs.avg_daily_peak = daily_peaks.mean()

    # Peak-to-average power ratio
    model_outputs.peak_to_average = (
            model.total_load.max() / model.total_load.mean()
    )
