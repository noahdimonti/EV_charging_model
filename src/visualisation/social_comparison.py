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

