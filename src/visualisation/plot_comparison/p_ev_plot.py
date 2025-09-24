import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pprint import pprint
from src.visualisation import plot_setups
from src.config import params, ev_params


def charging_power_plot(configurations, charging_strategies, version, save_img: False):
    all_results = []
    for config in configurations:
        for strategy in charging_strategies:
            results = plot_setups.get_model_results_data(config, strategy, version)

            # Capitalise config and strategy names
            config_name, config_num = config.split('_')
            config_name = config_name.capitalize()
            cap_config = f'{config_name} {config_num}'
            cap_strategy = strategy.capitalize()

            print(f'\n{cap_config} {cap_strategy}\n')

            for i in results.sets['EV_ID']:
                print(f'\nEV {i} arrival times:')
                pprint(ev_params.t_arr_dict[i])
                for t in results.sets['TIME']:
                    p_ev = results.variables['p_ev'][i, t]
                    if p_ev > 0:
                        all_results.append({
                            'config': config,
                            'strategy': strategy,
                            'EV_ID': i,
                            'time': t,
                            'charging_power': p_ev
                        })
                        # print(f'EV: {i}, time: {t}, charging power: {p_ev}')



    df = pd.DataFrame(all_results)
    print(df)

    # Create subplots: one per config
    fig, axes = plt.subplots(len(configurations), 1, figsize=(12, 4*len(configurations)), sharex=True, sharey=True)

    if len(configurations) == 1:
        axes = [axes]  # make it iterable

    for ax, config in zip(axes, df['config'].unique()):
        for strategy in df['strategy'].unique():
            sub = df[(df['config'] == config) & (df['strategy'] == strategy)]
            if sub.empty:
                continue
            sub['charging_flag'] = sub['charging_power'] > 0
            occupancy = sub.groupby('time')['charging_flag'].sum()

            ax.plot(
                occupancy.index, occupancy.values,
                label=strategy
            )

        ax.set_title(config)
        ax.set_xlabel('Time')
        ax.set_ylabel('Number of EVs charging')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(title='Strategy')

    plt.tight_layout()

    # Save plot
    if save_img:
        plot_setups.save_plot(f'charger_occupancy_{params.num_of_evs}EVs.png')





if __name__ == '__main__':
    charging_power_plot(
        ['config_1', 'config_2', 'config_3'],
        ['opportunistic', 'flexible'],
        'norm_w_sum',
        True
    )