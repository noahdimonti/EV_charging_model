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


def run_model(config, charging_strategy, time_limit=None):
    config_map = {
        'config_1': assets.CPConfig.CONFIG_1,
        'config_2': assets.CPConfig.CONFIG_2
    }

    strategy_map = {
        'opportunistic': assets.ChargingStrategy.OPPORTUNISTIC,
        'flexible': assets.ChargingStrategy.FLEXIBLE
    }

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

    model = assets.BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy],
        p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
        params=params,
        ev_params=ev_params,
        independent_vars=independent_variables
    ).get_model()

    # Solve model
    solved_model = solve_model.solve_optimisation_model(model, time_limit=time_limit)

    return solved_model


def iterate_models(configs, charging_strategies):
    for config in configs:
        for strategy in charging_strategies:
            config = config
            charging_strategy = strategy
            print(f'\n============= {config.value.capitalize()} - {strategy.value.capitalize()} Charging Strategy '
                  f'=============\n')

            model = assets.BuildModel(
                config=config,
                charging_strategy=charging_strategy,
                p_cp_rated_mode=assets.MaxChargingPower.VARIABLE,
                params=params,
                ev_params=ev_params,
                independent_vars=independent_variables
            ).get_model()

            solve_model.solve_optimisation_model(model)

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

