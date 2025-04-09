import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import setup_plot
from src.visualisation import plot_colours
from pprint import pprint


# def plot_dso_metrics_comparison(version: str, save_img=False):
#     metrics = setup_plot.get_metrics(version)
#     dso_metrics = metrics.loc[['avg_p_peak', 'avg_papr', 'avg_daily_peak_increase']]
#     avg_papr = metrics.loc['avg_papr']
#     avg_daily_peak_increase = metrics.loc['avg_daily_peak_increase']
#
#     print(dso_metrics)
#     print(avg_papr)
#     print(avg_daily_peak_increase)
#
#     # Define units for each metric
#     units = {
#         'avg_p_peak': 'kW',
#         'avg_papr': '',  # unitless
#         'avg_daily_peak_increase': '%'
#     }
#
#     ax = dso_metrics.T.plot(kind='bar', figsize=(10, 6))
#
#     plt.ylabel('Metric Value')
#     plt.xlabel('Model Configuration')
#     plt.title('Comparison of Metrics by Charging Strategy')
#     plt.xticks(rotation=45)
#     plt.grid(axis='y', linestyle='--', alpha=0.5)
#
#     # Add value labels with units
#     for idx, container in enumerate(ax.containers):
#         metric = dso_metrics.index[idx]
#         unit = units[metric]
#         ax.bar_label(container, labels=[f'{val.get_height():.3f} {unit}' for val in container], padding=3)
#
#     plt.tight_layout()
#
#     setup_plot.save_plot('test')
#     plt.show()


def demand_profiles(configurations: list, charging_strategies: list, version: str, save_img=False):
    # Create the plot
    fig, ax = plt.subplots(figsize=setup_plot.fig_size)

    # Plot household load
    house_load = [load for load in params.household_load['household_load']]
    ax.fill_between(params.timestamps, house_load, color=plot_colours.household_baseline_load, linewidth=1, alpha=0.6, label='Household Load')

    # Plot total demand
    for config in configurations:
        for strategy in charging_strategies:
            results = setup_plot.get_model_results_data(config, strategy, version)
            ev_load = [sum(results.variables['p_ev'][i, t] for i in results.sets['EV_ID']) for t in results.sets['TIME']]
            total_demand = [h_l + ev_l for h_l, ev_l in zip(house_load, ev_load)]
            ax.plot(
                params.timestamps,
                total_demand,
                color=plot_colours.models_colour_dict[f'{config}_{strategy}'],
                linewidth=1.5,
                label=f'{strategy.capitalize()} Charging Load')

    setup_plot.setup('Comparison of Charging Strategies Load Profiles', 'Load (kW)')

    if save_img:
        setup_plot.save_plot(f'demand_profiles_{version}')
    plt.show()


def soc_distribution(configurations: list, charging_strategies: list, version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = setup_plot.get_model_results_data(config, strategy, version)

            for i in results.sets['EV_ID']:
                for t in results.sets['TIME']:

                    if t in ev_params.t_arr_dict[i]:
                        soc_t_arr = (results.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100
                        all_results.append({
                            'config': config,
                            'strategy': strategy,
                            'model': f"{strategy.capitalize()} Charging",
                            'ev_id': i,
                            'time': t,
                            'soc_t_arr': soc_t_arr
                        })

    df_results = pd.DataFrame(all_results)
    print(df_results)

    # Violin plot with inner box
    plt.figure(figsize=(10, 6))
    sns.violinplot(x='model', y='soc_t_arr', hue='model', data=df_results, inner='box', palette='Set2', legend=False)

    plt.title('Distribution of SOC at Arrival')
    plt.ylabel('SOC at Arrival (%)')
    plt.xlabel('Model')
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.ylim(0, 100)
    plt.tight_layout()

    if save_img:
        setup_plot.save_plot(f'soc_distribution_{version}')
    plt.show()


def users_cost_distribution(configurations: list, charging_strategies: list, version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = setup_plot.get_model_results_data(config, strategy, version)

            # maintenance cost
            maintenance_cost_per_user = (params.annual_maintenance_cost / 365) * params.num_of_days

            # operational cost
            operational_cost_per_user = params.daily_supply_charge_dict[independent_variables.tariff_type] * params.num_of_days

            for i in results.sets['EV_ID']:
                total_cost_per_user = (sum(
                    params.tariff_dict[independent_variables.tariff_type][t] * results.variables['p_ev'][i, t]
                    for t in results.sets['TIME']
                ) + maintenance_cost_per_user + operational_cost_per_user)

                all_results.append({
                    'config': config,
                    'strategy': strategy,
                    'model': f"{strategy.capitalize()} Charging",
                    'ev_id': i,
                    'user_cost': total_cost_per_user
                })

    df_results = pd.DataFrame(all_results)
    print(df_results)

    # Violin plot with inner box
    plt.figure(figsize=(10, 6))
    ax = sns.boxplot(x='model', y='user_cost', hue='model', data=df_results, palette='Set2', legend=False, width=0.25)

    plt.title('Statistics of EV Charging Cost')
    plt.ylabel('Cost ($)')
    plt.xlabel('Model')
    plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()

    # Loop through the lines and modify thickness
    for line in ax.lines:
        line.set_linewidth(2.5)

    if save_img:
        setup_plot.save_plot(f'users_cost_distribution_{version}')
    plt.show()
