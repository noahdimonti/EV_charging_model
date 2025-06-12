import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def soc_distribution(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            for i in results.sets['EV_ID']:
                for t in results.sets['TIME']:

                    if t in ev_params.t_dep_dict[i]:
                        soc_t_dep = (results.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100
                        all_results.append({
                            'config': cap_config,
                            'strategy': cap_strategy,
                            'model': f'{cap_config} - {cap_strategy} Charging',
                            'ev_id': i,
                            'time': t,
                            'soc_t_dep': soc_t_dep
                        })

    df_results = pd.DataFrame(all_results)

    # Violin plot with inner box
    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.violinplot(
        x='config',
        y='soc_t_dep',
        hue='strategy',
        data=df_results,
        inner='box',
        palette='Set2'
    )

    plot_setups.setup(
        title='Distribution of SOC at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'soc_distribution_{params.num_of_evs}EVs_{version}')
    # plt.show()


def num_cp_plot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            # Define number of CP
            num_cp = int(results.variables['num_cp']) \
                if config != 'config_1' else params.num_of_evs

            # Scale rated power of CP
            p_cp_rated = results.variables['p_cp_rated'] * params.charging_power_resolution_factor

            all_results.append({
                'config': cap_config,
                'strategy': cap_strategy,
                'model': f'{cap_config} - {cap_strategy} Charging',
                'num_cp': num_cp,
                'p_cp_rated': p_cp_rated
            })

    df_results = pd.DataFrame(all_results)

    plt.figure(figsize=plot_setups.fig_size)

    ax = sns.barplot(
        x='config',
        y='num_cp',
        hue='strategy',
        data=df_results,
        palette='Set2'
    )

    plot_setups.setup(
        title='Number of Charging Points',
        ylabel='Number of Charging Points',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    # Add p_cp_rated labels on top of each bar
    for container in ax.containers:
        for bar, label in zip(container, df_results['p_cp_rated']):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + 0.125,  # adjust for spacing above bar
                f'{label} kW',  # or just `label` if not float
                ha='center',
                va='bottom',
                fontsize=plot_configs.tick_fontsize,
                fontweight='bold'
            )

    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_cp_plot_{params.num_of_evs}EVs_{version}')
    # plt.show()


def num_charging_day_plot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            avg_num_charging_days = results.metrics['avg_num_charging_days']

            all_results.append({
                'config': cap_config,
                'strategy': cap_strategy,
                'model': f'{cap_config} - {cap_strategy} Charging',
                'num_charging_day': avg_num_charging_days
            })

    df_results = pd.DataFrame(all_results)

    plt.figure(figsize=plot_setups.fig_size)

    ax = sns.barplot(
        x='config',
        y='num_charging_day',
        hue='strategy',
        data=df_results,
        palette='Set2'
    )

    plot_setups.setup(
        title='Average Number of Charging Days',
        ylabel='Average Number of Charging Days',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_cp_plot_{params.num_of_evs}EVs_{version}')
    # plt.show()

