import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def get_dso_metrics_df(configurations: list[str], charging_strategies: list[str], version: str, comparison_ver=None, comp_versions=None):
    all_results = []

    if comparison_ver == 'models_comparison':
        for config in configurations:
            for strategy in charging_strategies:
                results = plot_setups.get_model_results_data(config, strategy, version)

                # Capitalise config and strategy names
                config_name, config_num = config.split('_')
                config_name = config_name.capitalize()
                cap_config = f'{config_name} {config_num}'
                cap_strategy = strategy.capitalize()

                # Get peak demand increase and PAPR
                all_results.append({
                    'config': cap_config,
                    'strategy': cap_strategy,
                    'p_peak_increase': results.metrics['p_peak_increase'],
                    'papr': results.metrics['papr']
                })

    elif comparison_ver == 'objective_comparison':
        for version in comp_versions:
            p_peak_inc = []
            papr = []
            for config in configurations:
                for strategy in charging_strategies:
                    results = plot_setups.get_model_results_data(config, strategy, version)

                    p_peak_inc.append(results.metrics['p_peak_increase'])
                    papr.append(results.metrics['papr'])

            avg_p_peak_inc = np.average(p_peak_inc)
            avg_papr = np.average(papr)

            # Rename version
            cap_version_names_dict = {
                'norm_w_sum': 'Socio-techno-economic',
                'min_economic': 'Economic',
                'min_technical': 'Technical',
                'min_econ_tech': 'Techno-economic'
            }
            cap_version = cap_version_names_dict[version]

            all_results.append({
                'version': cap_version,
                'avg_p_peak_inc': avg_p_peak_inc,
                'avg_papr': avg_papr
            })

    else:
        raise ValueError("Invalid comparison_ver. Valid options: 'models_comparison' or 'objective_comparison'")

    df_results = pd.DataFrame(all_results)

    print(f'\nDSO metrics summary:\n')
    print(df_results)

    # Save dataframe
    filepath = os.path.join(params.metrics_folder_path, 'dso_metrics')
    filename = os.path.join(filepath, f'dso_metrics_{version}_{comparison_ver}')
    df_results.to_csv(filename)

    print(f'\nDSO metrics dataframe saved as csv to {filename}\n')

    return df_results


if __name__ == '__main__':
    get_dso_metrics_df(
        ['config_1', 'config_2', 'config_3'],
        # ['opportunistic', 'flexible'],
        ['uncoordinated', 'opportunistic', 'flexible'],
        'norm_w_sum',
        'models_comparison'
        # 'objective_comparison',
        # ['min_economic', 'min_technical', 'min_econ_tech', 'norm_w_sum']
    )







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
            xlabel='Day/Time',
            legend=True,
            legend_col=2,
            ax=ax
        )

        plot_setups.timeseries_setup(ax=ax)

    # Add space between subplots
    fig.subplots_adjust(hspace=0.3)

    if save_img:
        plot_setups.save_plot(f'demand_profiles_by_config_{params.num_of_evs}EVs_{version}')

    # plt.show()


def charging_strategy_load_delta_comparison(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    # Define grid size
    n_configs = len(configurations)

    # Define figure and axes
    fig, axes = plt.subplots(nrows=n_configs, ncols=1,
                             figsize=(plot_setups.fig_size[0], plot_setups.fig_size[1] * n_configs))
    axes = np.array(axes).reshape(-1)  # flatten in case nrows=1

    # Get household load data
    house_load = list(params.household_load['household_load'])

    colors = {
        'uncoordinated': 'tab:red',
        'opportunistic': 'tab:orange',
        'flexible': 'tab:blue'
    }

    # collect all deltas into a tidy dataframe
    records = []

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

        if 'uncoordinated' in charging_strategies:
            uncoordinated_results = plot_setups.get_model_results_data(config, 'uncoordinated', version)
            strategies = [s for s in charging_strategies if s != 'uncoordinated']
        else:
            raise ValueError('Uncoordinated strategy does not exist.')

        time_steps = list(uncoordinated_results.sets['TIME'])

        for strategy in strategies:
            strategy_results = plot_setups.get_model_results_data(config, strategy, version)
            load_delta = [
                strategy_results.variables['p_grid'][t] - strategy_results.variables['household_load'][t]
                for t in time_steps
            ]

            ax.plot(
                params.timestamps,
                load_delta,
                color=colors[strategy],
                linewidth=2,
                label=f'{strategy.capitalize()} Charging'
            )

            for t, delta in zip(time_steps, load_delta):
                records.append({
                    'Time': t,
                    'Delta': delta,
                    'Strategy': strategy
                })

        config_name, config_num = config.split('_')
        config_name = f'{config_name}uration'.capitalize()
        title = f'{config_name} {config_num}'

        # Call the unified plot setup
        plot_setups.setup(
            title=title,
            ylabel='Δ Load (Strategy – Uncoordinated)',
            xlabel='Day/Time',
            legend=True,
            legend_col=3,
            ax=ax
        )

        plot_setups.timeseries_setup(ax)

        # Add horizontal line on y=0
        ax.axhline(0, color='black', linewidth=2.5)

    # Add space between subplots
    fig.subplots_adjust(hspace=0.3)

    if save_img:
        plot_setups.save_plot(f'charging_strategy_delta_profiles_{params.num_of_evs}EVs_{version}')


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

