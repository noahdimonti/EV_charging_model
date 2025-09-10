import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups, plot_configs, social_comparison
from src.visualisation.social_comparison import get_wait_time_list
from pprint import pprint


def soc_stats(configurations: list[str], charging_strategies: list[str], versions: list[str], save_img=False):
    dfs = []
    for version in versions:
        df_results = social_comparison.get_soc_df(configurations, charging_strategies, version)

        # Rename version
        cap_version_names_dict = {
            'norm_w_sum': 'Socio-techno-economic',
            'min_economic': 'Economic',
            'min_technical': 'Technical',
            'min_econ_tech': 'Techno-economic'
        }
        cap_version = cap_version_names_dict[version]

        soc_col = df_results['soc_t_dep'].rename(cap_version)
        dfs.append(soc_col)

    df_concat = pd.concat(dfs, axis=1)

    # Melt into a long format
    df_long = df_concat.melt(
        var_name='version',
        value_name='soc_t_dep'
    )
    print(df_long)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='version',
        y='soc_t_dep',
        hue='version',
        data=df_long,
        legend=False,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'}  # bold black median line

    )

    plot_setups.setup(
        title='Aggregated SOC Distribution at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Minimised Objective',
        legend=False,
        ax=ax
    )

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'objective_comparison_soc_{params.num_of_evs}EVs_{version}')
    # plt.show()


def wait_time_distrib_stats(configurations: list[str], charging_strategies: list[str], versions: list[str], save_img=False):
    all_results = []
    for version in versions:
        for config in configurations:
            for strategy in charging_strategies:
                print('test')
                results = get_wait_time_list(config, strategy, version, all_results)
                all_results.extend(results)

    df_results = pd.DataFrame(all_results)
    print(df_results)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='version',
        y='wait_time',
        hue='version',
        data=df_results,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'}  # bold black median line

    )

    plot_setups.setup(
        title='Aggregated Charging Wait Time Distribution on Arrival',
        ylabel='Wait Time (hours)',
        xlabel='Minimised Objective',
        legend=False,
        ax=ax
    )

    if save_img:
        plot_setups.save_plot(f'wait_time_boxplot_{params.num_of_evs}EVs_{version}')
    # plt.show()


def peak_demand_stats(configurations: list[str], charging_strategies: list[str], versions: list[str], save_img=False):
    all_results = {}
    for version in versions:
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

        all_results[cap_version] = {
            'avg_p_peak_inc': avg_p_peak_inc,
            'avg_papr': avg_papr
        }

    pprint(all_results)
    df = pd.DataFrame(all_results).T.reset_index().rename(columns={'index': 'version'})
    df = df.melt(id_vars='version', var_name='metric', value_name='value')
    print(df)

    df = pd.DataFrame(all_results).T.reset_index().rename(columns={'index': 'version'})

    x = range(len(df))

    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Left axis (peak increase %)
    bars1 = ax1.bar(
        [i - 0.2 for i in x],
        df['avg_p_peak_inc'],
        width=0.4,
        label='Peak Increase (%)',
        color='tab:blue'
    )
    ax1.set_ylabel('Peak Increase (%)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_ylim(0, 4)

    # Right axis (PAPR)
    ax2 = ax1.twinx()
    bars2 = ax2.bar(
        [i + 0.2 for i in x],
        df['avg_papr'],
        width=0.4,
        label='PAPR (unitless)',
        color='tab:orange'
    )
    ax2.set_ylabel('PAPR (unitless)', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')
    ax2.set_ylim(0, 4)

    # X-axis labels
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['version'], rotation=15)

    # Legend
    # fig.legend(
    #     [bars1, bars2],
    #     ['Peak Increase (%)', 'PAPR (unitless)'],
    #     loc='upper right'
    # )

    # plt.figure(figsize=plot_setups.fig_size)
    # ax = sns.barplot(
    #     data=df,
    #     x='version',
    #     y='value',
    #     hue='metric',
    #     palette='Set2'
    # )
    #
    # plot_setups.setup(
    #     title='Demand profile statistics summary',
    #     ylabel='SOC at Departure Time (%)',
    #     xlabel='Minimised Objective',
    #     legend=False,
    #     ax=ax
    # )

    if save_img:
        plot_setups.save_plot(f'objective_comparison_dso_metrics_{params.num_of_evs}EVs_{version}')
    # plt.show()


wait_time_distrib_stats(
    ['config_1', 'config_2', 'config_3'],
    ['opportunistic', 'flexible'],
    ['min_economic', 'min_technical', 'min_econ_tech', 'norm_w_sum'],
    # True
)