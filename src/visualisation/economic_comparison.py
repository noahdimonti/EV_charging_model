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


def investment_cost(configurations: list[str], charging_strategies: list[str], version: str, save_img=False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            all_results.append({
                'config': cap_config,
                'strategy': cap_strategy,
                'model': f'{cap_config} - {cap_strategy} Charging',
                'investment_cost': float(results.metrics['investment_cost'])
            })

    df_results = pd.DataFrame(all_results)

    plt.figure(figsize=plot_setups.fig_size)

    ax = sns.barplot(
        x='config',
        y='investment_cost',
        hue='strategy',
        data=df_results,
        palette='Set2'
    )

    plot_setups.setup(
        title='Investment Cost of Models',
        ylabel='Investment Cost ($)',
        xlabel='Configuration',
        legend=True,
        ax=ax
    )

    # Set y-ticks range
    ax.yaxis.set_major_locator(ticker.MultipleLocator(400))

    # Save plot
    if save_img:
        plot_setups.save_plot(f'investment_cost_{params.num_of_evs}EVs_{version}')
    # plt.show()



