import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


def soc_distribution(configurations: list, charging_strategies: list, version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            for i in results.sets['EV_ID']:
                for t in results.sets['TIME']:

                    if t in ev_params.t_dep_dict[i]:
                        soc_t_dep = (results.variables['soc_ev'][i, t] / ev_params.soc_max_dict[i]) * 100
                        all_results.append({
                            'config': config,
                            'strategy': strategy,
                            'model': f'{config.capitalize()} - {strategy.capitalize()} Charging',
                            'ev_id': i,
                            'time': t,
                            'soc_t_dep': soc_t_dep
                        })

    df_results = pd.DataFrame(all_results)

    # Violin plot with inner box
    plt.figure(figsize=(plot_setups.fig_size))
    ax = sns.violinplot(x='model', y='soc_t_dep', hue='model', data=df_results, inner='box', palette='Set2', legend=False)

    plot_setups.setup(
        title='Distribution of SOC at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Model',
        legend=False,
        ax=ax
    )

    # Set y axis limits
    plt.ylim(0, 100)

    if save_img:
        plot_setups.save_plot(f'soc_distribution_{params.num_of_evs}EVs_{version}')
    plt.show()


def users_cost_distribution(configurations: list, charging_strategies: list, version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

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
                    'model': f'{config.capitalize()} - {strategy.capitalize()} Charging',
                    'ev_id': i,
                    'user_cost': total_cost_per_user
                })

    df_results = pd.DataFrame(all_results)

    # Violin plot with inner box
    plt.figure(figsize=(10, 6))
    ax = sns.boxplot(x='model', y='user_cost', hue='model', data=df_results, palette='Set2', legend=False, width=0.45)

    plot_setups.setup(
        title='Statistical Summary of EV Charging Cost',
        ylabel='Cost ($)',
        xlabel='Model',
        legend=False,
        ax=ax
    )

    # Add values of median, Q1, and Q3 to the plot
    groups = df_results.groupby('model')

    # Create a mapping of model names to positions on the x-axis
    xtick_labels = [tick.get_text() for tick in ax.get_xticklabels()]
    model_to_x = {model: i for i, model in enumerate(xtick_labels)}

    for model, group in groups:
        values = group['user_cost']
        q1 = values.quantile(0.25)
        median = values.median()
        q3 = values.quantile(0.75)
        xpos = model_to_x[model]

        # Add annotations to the plot
        ax.text(xpos, median + 0.5, f'Median: {median:.2f}', ha='center', va='bottom',
                fontsize=9, weight='bold', color='black')
        ax.text(
            xpos, q1 - 0.5, f'Q1: {q1:.2f}',
            ha='center', va='top',
            fontsize=9, weight='bold', color='black',
            bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.3', alpha=0.95)
        )

        ax.text(
            xpos, q3 + 0.5, f'Q3: {q3:.2f}',
            ha='center', va='bottom',
            fontsize=9, weight='bold', color='black',
            bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.3', alpha=0.95)
        )

    # Loop through the lines and modify whiskers thickness
    for line in ax.lines:
        line.set_linewidth(2.5)

    if save_img:
        plot_setups.save_plot(f'users_cost_distribution_{params.num_of_evs}EVs_{version}')
    plt.show()
