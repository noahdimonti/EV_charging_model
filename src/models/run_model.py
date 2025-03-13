import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import configs
import build_model
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from src.utils.evaluation_metrics import ModelResults
from pprint import pprint


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

    # Add title
    fig.suptitle(f'{model.name}', fontsize=16)

    # Adjust layout
    plt.tight_layout(pad=3)

    plt.show()


def run(config: str,
        charging_strategy: str,
        verbose=False,
        time_limit=None,
        mip_gap=None,
        plot=False):
    config_map = {
        'config_1': configs.CPConfig.CONFIG_1,
        'config_2': configs.CPConfig.CONFIG_2,
        'config_3': configs.CPConfig.CONFIG_3,
    }

    strategy_map = {
        'opportunistic': configs.ChargingStrategy.OPPORTUNISTIC,
        'flexible': configs.ChargingStrategy.FLEXIBLE
    }

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

    model = build_model.BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy],
        p_cp_rated_mode=configs.MaxChargingPower.VARIABLE,
        params=params,
        ev_params=ev_params,
        independent_vars=independent_variables
    ).get_model()

    # Solve model
    solved_model = solve_model.solve_optimisation_model(model, verbose=verbose, time_limit=time_limit, mip_gap=mip_gap)

    print(
        f'{config_map[config].value.capitalize()} - {strategy_map[charging_strategy].value.capitalize()} Charging '
        f'Strategy Results Summary')
    print(f'---------------------------------------------------------')

    # Model results
    model_results = ModelResults(strategy_map[charging_strategy], model, params, ev_params, independent_variables)
    econ_metric = model_results.get_economic_metrics()
    tech_metric = model_results.get_technical_metrics()
    soc_metric = model_results.get_social_metrics()

    if strategy_map[charging_strategy].value == 'flexible':
        model.num_charging_days.display()

    if plot:
        plot_results(solved_model)

    return solved_model


def iterate_models(configurations: list,
                   charging_strategies: list,
                   verbose=False,
                   time_limit=None,
                   mip_gap=None,
                   plot=False):
    for config in configurations:
        for strategy in charging_strategies:
            model = run(config, strategy, verbose=verbose, time_limit=time_limit, mip_gap=mip_gap, plot=plot)

            return model
