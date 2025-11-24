import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

import math
from src.config import params, ev_params
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def get_soc_df(configurations, charging_strategies, version):
    # Get a compilation of SOC for ONE version: for 7 days, ALL EVs, concatenated across ALL configurations and strategies.
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


def get_wait_time_list(config, strategy, version):
    results = plot_setups.get_model_results_data(config, strategy, version)
    results_list = []

    # Capitalise config and strategy names
    config_name, config_num = config.split('_')
    config_name = config_name.capitalize()
    cap_config = f'{config_name} {config_num}'
    cap_strategy = strategy.capitalize()

    # print(f'\n{config} {strategy}\n')

    t_arr_count = 0
    for i in results.sets['EV_ID']:
        for t_arr in ev_params.t_arr_dict[i]:
            # print(f'EV ID {i}, t_arr: {t_arr}')
            soc_t_arr = (results.variables['soc_ev'][i, t_arr] / ev_params.soc_max_dict[i]) * 100
            wait_time = None

            t_arr_count += 1
            # search for the first charging time >= t
            for future_t in results.sets['TIME']:
                if future_t >= t_arr and results.variables['p_ev'][i, future_t] > 0:
                    delta = future_t - t_arr
                    wait_time = round((delta.total_seconds() / 3600), 2)  # in hours
                    # print(f'EV {i}, arrival time: {t_arr}, current time: {future_t}, wait time: {wait_time}, '
                    #       f'soc t arr: {soc_t_arr}, soc current time: {(results.variables['soc_ev'][i, future_t] / ev_params.soc_max_dict[i]) * 100}')
                    break  # stop at the first charging event

            results_list.append({
                'config': cap_config,
                'strategy': cap_strategy,
                'model': f'{cap_config} - {cap_strategy} Charging',
                'version': version,
                'wait_time': wait_time,
            })

    return results_list



def soc_boxplot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    df_results = get_soc_df(configurations, charging_strategies, version)

    # Rename config column values to only numbers
    df_results['config_num'] = df_results['config'].str.extract(r'(\d+)').astype(int)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='config_num',
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

    # Adjust x tick label size
    ax.tick_params(axis='x', labelsize=20)

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'soc_boxplot_{params.num_of_evs}EVs_{version}')
    # plt.show()


def num_charging_days_plot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
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

    # Rename config column values to only numbers
    df_results['config_num'] = df_results['config'].str.extract(r'(\d+)').astype(int)

    plt.figure(figsize=plot_setups.fig_size)

    ax = sns.barplot(
        x='config_num',
        y='num_charging_day',
        hue='strategy',
        data=df_results,
        palette='Set2'
    )

    plot_setups.setup(
        title='Number of Charging Days Comparison',
        ylabel='Average Number of Charging Days',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    # Adjust x tick label size
    ax.tick_params(axis='x', labelsize=20)

    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_charging_day_plot_{params.num_of_evs}EVs_{version}')
    # plt.show()


def num_charging_days_distrib(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            for val in results.num_charging_days.values():
                all_results.append({
                    'config': cap_config,
                    'strategy': cap_strategy,
                    'model': f'{cap_config} - {cap_strategy} Charging',
                    'num_charging_day': val
                })

    df_results = pd.DataFrame(all_results)

    # FacetGrid: one subplot per config
    g = sns.FacetGrid(df_results, col='config', hue='strategy',
                      col_wrap=3, sharex=True, sharey=True, palette='Set2')

    g.map(sns.histplot, 'num_charging_day', bins=range(0, 9), multiple='dodge', shrink=0.8)

    g.set_axis_labels('Number of Charging Days per Week', 'Count')
    # g.fig.text(0.5, 0.02, 'Number of Charging Days per Week', ha='center', fontsize=12, fontweight='bold')
    g.set_titles('{col_name}', weight='bold')
    g.add_legend(title='Strategy')

    # tidy up
    for ax in g.axes.flat:
        ax.set_xticks(range(0, 8))
        ax.grid(axis='y', linestyle='--', alpha=0.3)

    plt.subplots_adjust(top=0.8)
    g.fig.suptitle('Distribution of Number of Charging Days per Week', fontsize=14, fontweight='bold')


    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_charging_day_distribution_{params.num_of_evs}EVs_{version}')
    # plt.show()




def wait_time_histogram(configurations: list[str],
                        charging_strategies: list[str],
                        version: str,
                        save_img: bool = False):
    pd.options.display.max_columns = None
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = get_wait_time_list(config, strategy, version)
            all_results.extend(results)

    df_results = pd.DataFrame(all_results)
    print(df_results)
    df_results = df_results.dropna(subset=['wait_time'])
    print(df_results)

    for config in configurations:
        conf, num = config.split('_')
        conf = conf.capitalize()
        df = df_results[df_results['config'] == f'{conf} {num}']
        print(df)

    n_configs = len(configurations)
    fig, axes = plt.subplots(
        n_configs, 1,
        figsize=(8, 4 * n_configs),
        sharex=True
    )

    if n_configs == 1:
        axes = [axes]

    for ax, config in zip(axes, configurations):
        config, config_num = config.split('_')
        cap_config = config.capitalize()

        df_config = df_results[df_results['config'] == f'{cap_config} {config_num}']
        # print(df_config)

        sns.histplot(
            data=df_config,
            x='wait_time',
            hue='strategy',
            multiple='dodge',   # separate bars per strategy
            bins=20,
            palette='Set2',
            ax=ax
        )

        ax.set_title(f'{cap_config}uration {config_num}', fontweight='bold')
        ax.set_ylabel('Count')

        # Modify legend title and make it bold
        legend = ax.get_legend()
        if legend is not None:
            legend.set_title('Charging Strategy')
            legend.get_title().set_fontweight('bold')

    # show ticks on all subplots
    for ax in axes:
        ax.tick_params(axis='x', labelbottom=True)

    axes[-1].set_xlabel('Wait Time (hours)', fontweight='bold')
    plt.tight_layout()

    if save_img:
        plot_setups.save_plot(f'wait_time_hist_{params.num_of_evs}EVs_{version}.png')
    # plt.show()





def wait_time_boxplot(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    pd.options.display.max_columns = None
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = get_wait_time_list(config, strategy, version)
            all_results.extend(results)

    df_results = pd.DataFrame(all_results)
    filepath = os.path.join(params.metrics_folder_path, 'wait_time_data.csv')
    df_results.to_csv(filepath)
    print(f'csv saved to {filepath}')

    # Rename config column values to only numbers
    df_results['config_num'] = df_results['config'].str.extract(r'(\d+)').astype(int)

    for config in configurations:
        conf, num = config.split('_')
        conf = conf.capitalize()
        df = df_results[df_results['config'] == f'{conf} {num}']
        print(df)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='config_num',
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

    # Adjust x tick label size
    ax.tick_params(axis='x', labelsize=20)

    if save_img:
        plot_setups.save_plot(f'wait_time_boxplot_{params.num_of_evs}EVs_{version}')
    # plt.show()



if __name__ == '__main__':
    num_charging_days_plot(
        ['config_1', 'config_2', 'config_3'],
        ['uncoordinated', 'opportunistic', 'flexible'],
        'norm_w_sum',
        True
    )




# def soc_distribution(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
#     df_results = get_soc_df(configurations, charging_strategies, version)
#
#     # Subplots: one per config
#     n_configs = len(configurations)
#     fig, axes = plt.subplots(
#         n_configs, 1,
#         figsize=(plot_setups.fig_size[0], plot_setups.fig_size[1] * n_configs),
#         sharex=True
#     )
#
#     if n_configs == 1:
#         axes = [axes]  # make iterable
#
#     for idx, config in enumerate(df_results['config'].unique()):
#         ax = axes[idx]
#         sns.histplot(
#             x='soc_t_dep',
#             hue='strategy',
#             data=df_results[df_results['config'] == config],
#             multiple='dodge',
#             bins=20,
#             shrink=0.8,
#             palette='Set2',
#             ax=ax,
#             legend=(idx == 0)
#         )
#
#         # Configure the legend size and style
#         # Get the legend that Seaborn made
#         legend = ax.get_legend()
#         if legend:
#             legend.set_title('Charging Strategy')
#             legend.get_title().set_fontsize(15)
#             legend.get_title().set_fontweight('bold')
#
#             for text in legend.get_texts():
#                 text.set_fontsize(14)
#                 text.set_fontweight('bold')
#
#             # Adjust spacing
#             legend._legend_box.align = 'left'  # optional: align entries nicely
#             legend.handletextpad = 2.5  # space between marker/line and text
#             legend.labelspacing = 2.5  # vertical space between legend entries
#
#         # Tick labels
#         ax.tick_params(axis='x', labelbottom=True)
#
#         plot_setups.setup(
#             title=f'{config}',
#             ylabel='Count',
#             xlabel='SOC Distribution at Departure Time (%)',
#             legend=False,
#             ax=ax
#         )
#
#         ax.set_xlim(0, 100)  # SOC % range
#
#     plt.tight_layout()
#
#     # Set y axis limits
#     plt.ylim(0, 100)
#
#     if save_img:
#         plot_setups.save_plot(f'soc_distribution_{params.num_of_evs}EVs_{version}')
#     # plt.show()

