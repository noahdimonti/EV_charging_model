import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params
from src.visualisation import plot_setups
from src.visualisation.plot_comparison import social_comparison
from src.visualisation.plot_comparison.social_comparison import get_wait_time_list
from pprint import pprint

# Rename version
cap_version_names_dict = {
    'norm_w_sum': 'Socio-techno-economic',
    'min_econ': 'Economic',
    'min_tech': 'Technical',
    'min_soc': 'Social',
    'econ_tech_pair': 'Techno-economic',
    'tech_soc_pair': 'Socio-technical',
    'econ_soc_pair': 'Socio-economic'
}


def get_soc_stats(configurations: list[str], charging_strategies: list[str], versions: list[str]):
    dfs = []
    for version in versions:
        df_results = social_comparison.get_soc_df(configurations, charging_strategies, version)

        cap_version = cap_version_names_dict[version]

        soc_col = df_results['soc_t_dep'].rename(cap_version)
        dfs.append(soc_col)

    df_concat = pd.concat(dfs, axis=1)

    # Melt into a long format
    df_long = df_concat.melt(
        var_name='version',
        value_name='soc_t_dep'
    )

    # Save results
    filepath = os.path.join(params.plots_folder_path, 'comparison_plots')
    filename = os.path.join(filepath, f'objective_comparison_soc_{params.num_of_evs}EVs.csv')
    df_long.to_csv(filename)
    print(f'csv saved to {filename}')

    return df_long


def soc_distrib_obj_comparison(configurations: list[str], charging_strategies: list[str], versions: list[str], save_img=False):
    df_long = get_soc_stats(configurations, charging_strategies, versions)

    plt.figure(figsize=plot_setups.fig_size)
    ax = sns.boxplot(
        x='version',
        y='soc_t_dep',
        hue='version',
        data=df_long,
        legend=False,
        palette='tab10',
        medianprops={'linewidth': 2.5, 'color': 'black'}  # bold black median line

    )

    plot_setups.setup(
        title='Aggregated SOC Distribution at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Objective',
        legend=False,
        ax=ax
    )

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'objective_comparison_soc_{params.num_of_evs}EVs.png')
    # plt.show()



def soc_stats_df(configurations: list[str], charging_strategies: list[str], versions: list[str]):
    df_long = get_soc_stats(configurations, charging_strategies, versions)

    # Get SOC average
    soc_avg = df_long.groupby('version', as_index=False, sort=False)['soc_t_dep'].mean()
    soc_avg = soc_avg.rename(columns={'soc_t_dep': 'soc_avg'})

    # Get SOC lowest
    lowest_soc = df_long.groupby('version', as_index=False, sort=False)['soc_t_dep'].min()
    lowest_soc = lowest_soc.rename(columns={'soc_t_dep': 'lowest_soc'})

    result = pd.merge(soc_avg, lowest_soc, on='version')
    print(result)


def dso_stats_df(configurations: list[str], charging_strategies: list[str], versions: list[str]):
    all_results = []
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

        cap_version = cap_version_names_dict[version]

        all_results.append({
            'version': cap_version,
            'avg_p_peak_inc': avg_p_peak_inc,
            'avg_papr': avg_papr
        })

    df_results = pd.DataFrame(all_results)
    print(df_results)

    # Save dataframe
    # filepath = os.path.join(params.metrics_folder_path, 'dso_metrics')
    # filename = os.path.join(filepath, f'dso_metrics_{version}_{comparison_ver}')
    # df_results.to_csv(filename)

    # print(f'\nDSO metrics dataframe saved as csv to {filename}')


def econ_stats_df(configurations: list[str], charging_strategies: list[str], versions: list[str]):
    all_results = []
    for version in versions:
        num_cp = []
        p_cp_rated = []

        for config in configurations:
            for strategy in charging_strategies:
                results = plot_setups.get_model_results_data(config, strategy, version)

                num_cp.append(results.metrics['num_cp'])
                p_cp_rated.append(results.metrics['p_cp_rated'])

        cap_version = cap_version_names_dict[version]

        all_results.append({
            'version': cap_version,
            'num_cp': np.average(num_cp),
            'p_cp_rated': np.average(p_cp_rated)
        })

    df = pd.DataFrame(all_results)
    print(df)




def wait_time_distrib_stats(configurations: list[str], charging_strategies: list[str], versions: list[str], save_img=False):
    all_results = []
    filepath = os.path.join(params.plots_folder_path, 'comparison_plots')
    filename = os.path.join(filepath, f'objective_comparison_wait_time_distribution_{params.num_of_evs}EVs')

    if not os.path.exists(filename):
        for version in versions:
            for config in configurations:
                for strategy in charging_strategies:
                    print(f'Fetching data for {version} version, {config}, {strategy} ...')
                    results = get_wait_time_list(config, strategy, version, all_results)
                    all_results.extend(results)

        print(f'Creating a dataframe ...')
        df_results = pd.DataFrame(all_results)
        # df_results = pd.DataFrame(
        #     all_results,
        #     columns=['config', 'strategy', 'model', 'version', 'ev_id', 'time', 'wait_time', 'soc_t_arr']
        # )
        print(df_results)

        # Save results
        # df_results.to_csv(filename)
        # print(f'csv saved to {filename}')

    else:
        df_results = pd.read_csv(filename)

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
        plot_setups.save_plot(f'objective_comparison_wait_time_boxplot_{params.num_of_evs}EVs_{version}')
    # plt.show()


if __name__ == '__main__':
    configs = [
        'config_1',
        'config_2',
        'config_3'
        ]

    strategies = [
        'opportunistic',
        'flexible'
        ]

    versions = [
            'min_econ',
            'min_tech',
            'min_soc',
            'econ_tech_pair',
            'tech_soc_pair',
            'econ_soc_pair',
            'norm_w_sum'
        ]

    dso_stats_df(configs, strategies, versions)
    #
    # soc_stats_df(configs, strategies, versions)
    #
    # econ_stats_df(configs, strategies, versions)

    soc_distrib_obj_comparison(configs, strategies, versions, True)

    # wait_time_distrib_stats(configs, strategies, versions)


