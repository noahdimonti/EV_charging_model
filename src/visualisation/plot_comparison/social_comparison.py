import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def get_soc_df(configurations, charging_strategies, version):
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

    return pd.DataFrame(all_results)


def get_wait_time_list(config, strategy, version, all_results: list):
    results = plot_setups.get_model_results_data(config, strategy, version)

    # Capitalise config and strategy names
    config_name, config_num = config.split('_')
    config_name = config_name.capitalize()
    cap_config = f'{config_name} {config_num}'
    cap_strategy = strategy.capitalize()

    for i in results.sets['EV_ID']:
        for t in ev_params.t_arr_dict[i]:
            soc_t_arr = (results.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100

            wait_time = None

            # search for the first charging time >= t
            for future_t in results.sets['TIME']:
                if future_t >= t and results.variables['p_ev'][i, future_t] > 0:
                    delta = future_t - t
                    wait_time = round((delta.total_seconds() / 3600), 2)  # in hours
                    break  # stop at the first charging event

            all_results.append({
                'config': cap_config,
                'strategy': cap_strategy,
                'model': f'{cap_config} - {cap_strategy} Charging',
                'version': version,
                'ev_id': i,
                'time': t,
                'wait_time': wait_time,
                'soc_t_arr': soc_t_arr
            })

    return all_results


def soc_distribution(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    df_results = get_soc_df(configurations, charging_strategies, version)

    # Subplots: one per config
    n_configs = len(configurations)
    fig, axes = plt.subplots(
        n_configs, 1,
        figsize=(plot_setups.fig_size[0], plot_setups.fig_size[1] * n_configs),
        sharex=True
    )

    if n_configs == 1:
        axes = [axes]  # make iterable

    for idx, config in enumerate(df_results['config'].unique()):
        ax = axes[idx]
        sns.histplot(
            x='soc_t_dep',
            hue='strategy',
            data=df_results[df_results['config'] == config],
            multiple='dodge',
            bins=20,
            shrink=0.8,
            palette='Set2',
            ax=ax,
            legend=(idx == 0)
        )

        # Configure the legend size and style
        # Get the legend that Seaborn made
        legend = ax.get_legend()
        if legend:
            legend.set_title('Charging Strategy')
            legend.get_title().set_fontsize(15)
            legend.get_title().set_fontweight('bold')

            for text in legend.get_texts():
                text.set_fontsize(14)
                text.set_fontweight('bold')

            # Adjust spacing
            legend._legend_box.align = 'left'  # optional: align entries nicely
            legend.handletextpad = 2.5  # space between marker/line and text
            legend.labelspacing = 2.5  # vertical space between legend entries

        # Tick labels
        ax.tick_params(axis='x', labelbottom=True)

        plot_setups.setup(
            title=f'{config}',
            ylabel='Count',
            xlabel='SOC Distribution at Departure Time (%)',
            legend=False,
            ax=ax
        )

        ax.set_xlim(0, 100)  # SOC % range

    plt.tight_layout()

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'soc_distribution_{params.num_of_evs}EVs_{version}')
    # plt.show()


def soc_boxplot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    df_results = get_soc_df(configurations, charging_strategies, version)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='config',
        y='soc_t_dep',
        hue='strategy',
        data=df_results,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'}  # bold black median line

    )

    plot_setups.setup(
        title='Distribution of SOC at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    plt.tight_layout()

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'soc_boxplot_{params.num_of_evs}EVs_{version}')
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
        plot_setups.save_plot(f'num_charging_day_plot_{params.num_of_evs}EVs_{version}')
    # plt.show()


def wait_time_distribution(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = get_wait_time_list(config, strategy, version, all_results)
            all_results.extend(results)

    df_results = pd.DataFrame(all_results)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='config',
        y='wait_time',
        hue='strategy',
        data=df_results,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'}  # bold black median line

    )

    plot_setups.setup(
        title='Distribution of Charging Wait Time on Arrival',
        ylabel='Wait Time (hours)',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    if save_img:
        plot_setups.save_plot(f'wait_time_boxplot_{params.num_of_evs}EVs_{version}')
    # plt.show()



wait_time_distribution(
    ['config_1', 'config_2', 'config_3'],
    ['uncoordinated', 'opportunistic', 'flexible'],
    'norm_w_sum',
    True
)