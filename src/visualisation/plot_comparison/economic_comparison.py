import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


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

    # Flatten the DataFrame in the same order as the bars are drawn
    # Seaborn draws bars for each hue in order for each x
    configs = df_results['config'].unique()
    strategies = df_results['strategy'].unique()

    # Loop over bars in order
    bars = [bar for container in ax.containers for bar in container]
    labels = []

    for config in configs:
        for strategy in strategies:
            # Select the matching row
            row = df_results[(df_results['config'] == config) & (df_results['strategy'] == strategy)]
            if not row.empty:
                labels.append(row['p_cp_rated'].values[0])

    # Add text labels on top of bars
    for bar, label in zip(bars, labels):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.125,
            f'{label} kW',
            ha='center',
            va='bottom',
            fontsize=plot_configs.tick_fontsize,
            fontweight='bold'
        )

    # Save plot
    if save_img:
        plot_setups.save_plot(f'num_cp_plot_{params.num_of_evs}EVs_{version}')
    # plt.show()






# def investment_cost(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
#     all_results = []
#     for config in configurations:
#         for strategy in charging_strategies:
#             results = plot_setups.get_model_results_data(config, strategy, version)
#
#             # Capitalise config and strategy names
#             config_name, config_num = config.split('_')
#             config_name = config_name.capitalize()
#             cap_config = f'{config_name} {config_num}'
#             cap_strategy = strategy.capitalize()
#
#             all_results.append({
#                 'config': cap_config,
#                 'strategy': cap_strategy,
#                 'model': f'{cap_config} - {cap_strategy} Charging',
#                 'investment_cost': float(results.metrics['investment_cost'])
#             })
#
#     df_results = pd.DataFrame(all_results)
#
#     plt.figure(figsize=plot_setups.fig_size)
#
#     ax = sns.barplot(
#         x='config',
#         y='investment_cost',
#         hue='strategy',
#         data=df_results,
#         palette='Set2'
#     )
#
#     plot_setups.setup(
#         title='Investment Cost of Models',
#         ylabel='Investment Cost ($)',
#         xlabel='Configuration',
#         legend=True,
#         ax=ax
#     )
#
#     # Set y-ticks range
#     ax.yaxis.set_major_locator(ticker.MultipleLocator(400))
#
#     # Save plot
#     if save_img:
#         plot_setups.save_plot(f'investment_cost_{params.num_of_evs}EVs_{version}')
#     # plt.show()
