import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def demand_profiles_by_config(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    # Define grid size
    n_configs = len(configurations)

    # Define figure and axes
    fig, axes = plt.subplots(nrows=n_configs, ncols=1,
                             figsize=(plot_setups.fig_size[0], plot_setups.fig_size[1] * n_configs))
    axes = np.array(axes).reshape(-1)  # flatten in case nrows=1

    # Get household load data
    house_load = list(params.household_load['household_load'])

    for idx, config in enumerate(configurations):
        ax = axes[idx]

        # Plot household base load
        ax.fill_between(
            params.timestamps,
            house_load,
            color=plot_configs.household_baseline_load,
            alpha=0.4,
            label='Household Load'
        )

        # Plot each strategy for the current config
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)
            ev_load = [sum(results.variables['p_ev'][i, t] for i in results.sets['EV_ID']) for t in
                       results.sets['TIME']]
            total_demand = [h + e for h, e in zip(house_load, ev_load)]

            ax.plot(
                params.timestamps,
                total_demand,
                color=plot_configs.models_colour_dict[f'{config}_{strategy}'],
                linewidth=1.5,
                label=f'{strategy.capitalize()} Charging'
            )

        config_name, config_num = config.split('_')
        config_name = f'{config_name}uration'.capitalize()
        title = f'{config_name} {config_num}'

        # Call the unified plot setup
        plot_setups.setup(
            title=title,
            ylabel='Load (kW)',
            xlabel='Day',
            legend=True,
            legend_col=3,
            ax=ax
        )

        plot_setups.timeseries_setup(ax=ax)

    # Add space between subplots
    fig.subplots_adjust(hspace=0.3)

    if save_img:
        plot_setups.save_plot(f'demand_profiles_by_config_{params.num_of_evs}EVs_{version}')

    # plt.show()


def demand_profiles_overlay(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    # Create the plot
    fig, ax = plt.subplots(figsize=plot_setups.fig_size)

    # Plot household load
    house_load = [load for load in params.household_load['household_load']]
    ax.fill_between(params.timestamps, house_load, color=plot_configs.household_baseline_load, linewidth=1, alpha=0.6, label='Household Load')

    # Plot total demand
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)
            ev_load = [sum(results.variables['p_ev'][i, t] for i in results.sets['EV_ID']) for t in results.sets['TIME']]
            total_demand = [h_l + ev_l for h_l, ev_l in zip(house_load, ev_load)]
            ax.plot(
                params.timestamps,
                total_demand,
                color=plot_configs.models_colour_dict[f'{config}_{strategy}'],
                linewidth=1.5,
                label=f'{config.capitalize()} - {strategy.capitalize()} Charging Load')

    plot_setups.setup(
        title='Comparison of Charging Strategies Load Profiles',
        ylabel='Load (kW)',
        xlabel='Day',
        legend=True,
        ax=ax
    )

    plot_setups.timeseries_setup(ax=ax)

    if save_img:
        plot_setups.save_plot(f'demand_profiles_{params.num_of_evs}EVs_{version}')
    # plt.show()

