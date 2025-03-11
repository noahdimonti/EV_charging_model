import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import assets
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from src.utils.evaluation_metrics import ModelResults
from pprint import pprint


def main():
    # Config setup
    # config = 'config_1'
    config = 'config_2'

    # Create the optimisation model
    if config == 'config_1':
        config_1_opportunistic = assets.BuildModel(
            config=assets.CPConfig.CONFIG_1,
            charging_strategy=assets.ChargingStrategy.OPPORTUNISTIC,
            p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
            params=params,
            ev_params=ev_params,
            independent_vars=independent_variables
        ).get_model()

        config_1_flexible = assets.BuildModel(
            config=assets.CPConfig.CONFIG_1,
            charging_strategy=assets.ChargingStrategy.FLEXIBLE,
            p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
            params=params,
            ev_params=ev_params,
            independent_vars=independent_variables
        ).get_model()

    elif config == 'config_2':
        config_2_opportunistic = assets.BuildModel(
            config=assets.CPConfig.CONFIG_2,
            charging_strategy=assets.ChargingStrategy.OPPORTUNISTIC,
            p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
            params=params,
            ev_params=ev_params,
            independent_vars=independent_variables
        ).get_model()

    # Solve model
    # model = config_1_flexible
    # model = config_1_opportunistic
    model = config_2_opportunistic
    solve_model.solve_optimisation_model(model)

    print(pyo.value(model.num_cp))
    model.num_cp.display()
    # print(model.ev_is_charging_at_cp_j.display())

    plot_results(model)

    # Display results
    # model.p_grid.display()
    # model.p_household_load.display()
    # model.p_cp.display()
    # model.p_ev.display()
    # model.soc_ev.display()

    # model.p_daily_peak.display()
    # model.p_daily_avg.display()
    # model.delta_daily_peak_avg.display()


def iterate_models():
    # charging_strategy = assets.ChargingStrategy.OPPORTUNISTIC
    for strategy in assets.ChargingStrategy:
        charging_strategy = strategy
        print(f'\n========== {strategy.value.capitalize()} Charging Strategy ==========\n')

        model = assets.BuildModel(
            config=assets.CPConfig.CONFIG_1,
            charging_strategy=charging_strategy,
            p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
            params=params,
            ev_params=ev_params,
            independent_vars=independent_variables
        ).get_model()

        solve_model.solve_optimisation_model(model)

        # print(pyo.value(model.p_cp_rated))

        model_results = ModelResults(charging_strategy, model, params, ev_params, independent_variables)
        econ_metric = model_results.get_economic_metrics()
        tech_metric = model_results.get_technical_metrics()
        soc_metric = model_results.get_social_metrics()
        pprint(econ_metric)
        pprint(tech_metric)
        pprint(soc_metric)


def plot_results(model):
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

    plt.show()


if __name__ == '__main__':
    main()
