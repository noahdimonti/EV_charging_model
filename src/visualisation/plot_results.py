import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.visualisation.plot_setups import fig_size
from src.config import params
from src.models.model_results import ModelResults


def plot_p_ev(results: ModelResults, save_img=False):
    p_ev_data = {i: [results.variables['p_ev'][i, t] for t in results.sets['TIME']] for i in results.sets['EV_ID']}

    plt.figure(figsize=fig_size)

    for i in results.sets['EV_ID']:
        plt.plot(params.timestamps, p_ev_data[i], linestyle='-', label=f'EV_{i}')

    # Use the helper function
    setup_plot(
        title='EV charging power',
        suptitle=f'{results.config.value.capitalize()} {results.charging_strategy.value.capitalize()} Charging - {params.num_of_evs} EVs',
        ylabel='Power (kW)'
    )

    # Save or show the plot
    if save_img:
        plt.savefig(
            f'../../reports/figures/p_ev_{results.config.value}_{results.charging_strategy.value}_{params.num_of_evs}EVs.png',
            dpi=300)

    plt.show()


def plot_agg_p_ev(results: ModelResults, save_img=False):
    plt.figure(figsize=fig_size)

    # Plot
    ev_load = [sum(results.variables['p_ev'][i, t] for i in results.sets['EV_ID']) for t in results.sets['TIME']]
    plt.plot(params.timestamps, ev_load, linestyle='-', label='EV_load')

    # Use the helper function
    setup_plot(
        title='EV charging power',
        suptitle=f'{results.config.value.capitalize()} {results.charging_strategy.value.capitalize()} Charging - {params.num_of_evs} EVs',
        ylabel='Power (kW)'
    )

    # Save or show the plot
    if save_img:
        plt.savefig(
            f'../../reports/figures/agg_p_ev-{results.config.value}_{results.charging_strategy.value}_{params.num_of_evs}EVs.png',
            dpi=300)

    plt.show()


def plot_agg_total_demand(results: ModelResults, save_img=False):
    # Create the plot
    fig, ax = plt.subplots(figsize=fig_size)

    # Plot household load
    house_load = [load for load in params.household_load['household_load']]
    ax.fill_between(params.timestamps, house_load, color='skyblue', linewidth=1, alpha=0.6, label='Household Load')

    # Plot total demand
    ev_load = [sum(results.variables['p_ev'][i, t] for i in results.sets['EV_ID']) for t in results.sets['TIME']]
    total_demand = [h_l + ev_l for h_l, ev_l in zip(house_load, ev_load)]
    ax.plot(params.timestamps, total_demand, color='orange', linewidth=1, label='Total Demand')

    # Plot peaks
    base_load_peak = max(house_load)
    total_load_peak = max(total_demand)

    ax.plot(params.timestamps, [base_load_peak for _ in params.timestamps], color='skyblue', linewidth=1, label='Base load peak')
    ax.plot(params.timestamps, [total_load_peak for _ in params.timestamps], color='orange', linewidth=1, label='Total load peak')

    # Add labels and title
    plt.ylabel('Power (kW)')
    plt.title('Total Demand')
    plt.suptitle(
        f'{results.config.value.capitalize()} {results.charging_strategy.value.capitalize()} Charging - {params.num_of_evs} EVs',
        fontsize=12, fontweight='bold')

    # Add grid
    plt.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.3)  # Grid for major ticks

    # Add top and right borders (spines)
    ax = plt.gca()
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')  # Set color of top border
    ax.spines['right'].set_color('black')  # Set color of right border
    ax.spines['top'].set_linewidth(1)  # Set line width for top border
    ax.spines['right'].set_linewidth(1)  # Set line width for right border

    # Add a legend outside the plot
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

    # Adjust the layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)

    # Save or show the plot
    if save_img:
        plt.savefig(
            f'../../reports/figures/agg_power_{results.config.value}_{results.charging_strategy.value}_{params.num_of_evs}EVs.png',
            dpi=300)

    plt.show()


def plot_ev_charging_schedule(results: ModelResults, save_img=False):
    # Convert the dictionary to a DataFrame
    df = pd.Series(results.variables['is_charging_day']).unstack(level=0).fillna(0)
    df.columns = [f'EV {i}' for i in df.columns]

    # Sort by date to ensure correct order
    df = df.sort_index()

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 6))

    # Stacked bar chart: Loop through each EV and plot their contribution
    bottom = np.zeros(len(df))  # To stack bars on top of each other

    for ev in df.columns:
        ax.bar(df.index, df[ev], bottom=bottom, label=ev)
        bottom += df[ev]  # Update bottom to stack the next EV

    # Title and Labels
    ax.set_title('EV Charging Schedule by Day', fontsize=16)
    ax.set_xlabel('Date')
    ax.set_ylabel('Charging Status')
    plt.suptitle(
        f'{results.config.value.capitalize()} {results.charging_strategy.value.capitalize()} Charging - {params.num_of_evs} EVs',
        fontsize=12, fontweight='bold')

    # Add top and right borders (spines)
    ax = plt.gca()
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')  # Set color of top border
    ax.spines['right'].set_color('black')  # Set color of right border
    ax.spines['top'].set_linewidth(1)  # Set line width for top border
    ax.spines['right'].set_linewidth(1)  # Set line width for right border

    # Add a legend outside the plot
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

    # Adjust the layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)

    # Save or show the plot
    if save_img:
        plt.savefig(
            f'../../reports/figures/ev_charging_schedule_{results.config.value}_{results.charging_strategy.value}_{params.num_of_evs}EVs.png',
            dpi=300)

    plt.show()


