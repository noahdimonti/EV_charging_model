import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os
from pprint import pprint
from src.visualisation import plot_setups, plot_configs
from src.config import params, ev_params


def get_p_ev_df(configurations, charging_strategies, version):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            print(f'\n{cap_config} {cap_strategy}\n')

            for i in results.sets['EV_ID']:
                print(f'\nEV {i} arrival times:')
                pprint(ev_params.t_arr_dict[i])
                for t in results.sets['TIME']:
                    p_ev = results.variables['p_ev'][i, t]
                    if p_ev > 0:
                        all_results.append({
                            'config': config,
                            'strategy': strategy,
                            'EV_ID': i,
                            'time': t,
                            'charging_power': p_ev
                        })
                        print(f'EV: {i}, time: {t}, charging power: {p_ev}')

    df = pd.DataFrame(all_results)
    print(df)

    return df


def num_ev_charging_plot(configurations, charging_strategies, version, save_img=False):
    df = get_p_ev_df(configurations, charging_strategies, version)

    # Define grid size
    n_configs = len(configurations)

    # Define figure and axes
    fig, axes = plt.subplots(nrows=n_configs, ncols=1,
                             figsize=(8, 5 * n_configs))
    axes = np.array(axes).reshape(-1)  # flatten in case nrows=1

    # Normalize axes -> always a flat list of Axes objects
    # When n_configs == 1, plt.subplots returns a single Axes, not an array
    axes = np.atleast_1d(axes).ravel().tolist()

    for idx, config in enumerate(configurations):
        ax = axes[idx]
        print(type(ax))

        for i, strategy in enumerate(charging_strategies):
            sub = df[(df['config'] == config) & (df['strategy'] == strategy)]
            if sub.empty:
                continue
            sub['charging_flag'] = sub['charging_power'] > 0
            occupancy = sub.groupby('time')['charging_flag'].sum()

            ax.step(
                occupancy.index,
                occupancy.values,
                where='post',
                label=strategy.capitalize()
            )

        config_name, config_num = config.split('_')
        config_name = f'{config_name}uration'.capitalize()
        title = f'{config_name} {config_num}'
        ylabel = 'Number of EVs charging'

        if n_configs == 1:
            title = f'Number of EVs Charging - Configuration {config_num}'
            ylabel = 'Count'

        # Call the unified plot setup
        plot_setups.setup(
            title=title,
            ylabel=ylabel,
            xlabel=None,
            legend=False,
            legend_col=2,
            ax=ax
        )

        plot_setups.timeseries_setup(ax=ax)

        # Set y axis limits
        ax.set_ylim(0, 11)

        if idx == n_configs-1:
            ax.set_xlabel('Day/Time', fontsize=plot_configs.label_fontsize, weight='bold')

            ax.legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.15),
                frameon=True,
                ncol=2,
                prop={
                    'weight': 'bold',
                    'size': plot_configs.legend_fontsize
                },
            )

    # Add space between subplots
    fig.subplots_adjust(hspace=0.5)
    plt.tight_layout()

    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_evs_charging_{params.num_of_evs}EVs_config{config_num}.png')


def p_ev_charging_plot(configurations, charging_strategies, version, save_img=False):
    df = get_p_ev_df(configurations, charging_strategies, version)

    # Define grid size
    n_configs = len(configurations)

    # Define figure and axes
    fig, axes = plt.subplots(nrows=n_configs, ncols=1,
                             figsize=(8, 5 * n_configs))
    axes = np.array(axes).reshape(-1)  # flatten in case nrows=1

    if len(configurations) == 1:
        axes = [axes]  # make it iterable

    for idx, config in enumerate(configurations):
        ax = axes[idx]

        for i, strategy in enumerate(charging_strategies):
            sub = df[(df['config'] == config) & (df['strategy'] == strategy)]
            if sub.empty:
                continue

            print(sub)

            ax.step(
                params.timestamps,
                sub.charging_power,
                where='post',
                label=strategy.capitalize()
            )

        config_name, config_num = config.split('_')
        config_name = f'{config_name}uration'.capitalize()
        title = f'{config_name} {config_num}'

        # Call the unified plot setup
        plot_setups.setup(
            title=title,
            ylabel='Number of EVs charging',
            xlabel=None,
            legend=False,
            legend_col=2,
            ax=ax
        )

        plot_setups.timeseries_setup(ax=ax)

        # Set y axis limits
        ax.set_ylim(0, 11)

        if idx == n_configs - 1:
            ax.set_xlabel('Day/Time', fontsize=plot_configs.label_fontsize, weight='bold')

            ax.legend(
                loc='upper center',
                bbox_to_anchor=(0.5, -0.15),
                frameon=True,
                ncol=2,
                prop={
                    'weight': 'bold',
                    'size': plot_configs.legend_fontsize
                },
            )

    # Add space between subplots
    fig.subplots_adjust(hspace=0.5)
    plt.tight_layout()

    # Save plot
    if save_img:
        plot_setups.save_plot(f'p_ev_charging_{params.num_of_evs}EVs.png')


if __name__ == '__main__':
    num_ev_charging_plot(
        ['config_2'],
        ['opportunistic', 'flexible'],
        'norm_w_sum',
        True
    )