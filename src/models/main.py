import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import assets
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from pprint import pprint


def main():
    # Create the optimization model
    config_1_opportunistic = assets.BuildModel(
        config=assets.CPConfig.CONFIG_1,
        charging_strategy=assets.ChargingStrategy.OPPORTUNISTIC,
        p_cp_max_mode=assets.MaxChargingPower.VARIABLE,
        params=params,
        ev_params=ev_params,
        independent_vars=independent_variables
    ).get_model()

    config_1_flexible = assets.BuildModel(
        config=assets.CPConfig.CONFIG_1,
        charging_strategy=assets.ChargingStrategy.FLEXIBLE,
        p_cp_max_mode=assets.MaxChargingPower.L_1,
        params=params,
        ev_params=ev_params,
        independent_vars=independent_variables
    ).get_model()

    # Solve model
    # model = config_1_flexible
    model = config_1_opportunistic
    # model.minimum_required_soc_at_departure_constraint.display()
    solve_model.solve_optimisation_model(model)

    # Display results
    # model.p_grid.display()
    # model.p_household_load.display()
    # model.p_cp.display()
    # model.p_ev.display()
    # model.soc_ev.display()

    # model.p_peak.display()
    # model.p_avg.display()
    # model.delta_peak_avg.display()

    model.config_1_ev_cp_mapping.display()

    if model == config_1_flexible:
        model.num_charging_days.display()
        # model.is_charging_day.display()
        for d in model.DAY:
            print(f'Day: {d}, Num of EVs charging: {sum(pyo.value(model.is_charging_day[i, d]) for i in model.EV_ID)}')

        for i in model.EV_ID:
            print(f'EV_ID: {i}, Num of charging days: {pyo.value(model.num_charging_days[i, 8])}')

    print(f'Charger rated power: {pyo.value(model.p_cp_max * params.charging_power_resolution_factor)} kW')

    soc_data = {i: [pyo.value(model.soc_ev[i, t]) for t in model.TIME] for i in model.EV_ID}
    p_ev_data = {i: [pyo.value(model.p_ev[i, t]) for t in model.TIME] for i in model.EV_ID}

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(5, 10), sharex=True)

    for i in model.EV_ID:
        axes[0].plot(params.timestamps, p_ev_data[i], linestyle='-', label=f'EV_{i}')
        axes[1].plot(params.timestamps, soc_data[i], linestyle='-', label=f'EV_{i}')

    axes[0].set_ylabel('Charging Power (kW)')
    axes[1].set_ylabel('SOC (kWh)')
    axes[0].legend()
    axes[1].legend()

    # Common X label
    axes[-1].set_xlabel("Time Steps")

    # plt.show()


if __name__ == '__main__':
    main()
