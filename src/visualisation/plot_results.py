import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.config import params

# graph colours
household_load_colour = 'red'
ev_load_colour = 'black'
total_load_colour = '#00cc96'
avg_daily_peak_colour = 'blue'


def plot_results(model_output):
    plt.style.use('default')

    fig, ax = plt.subplots(figsize=(12, 8))  # Adjust size for presentation

    # Plot EV load
    ax.plot(params.timestamps, model_output.ev_load, label='EV Load', color='blue', linewidth=2)

    # Plot peak EV load
    ax.plot(params.timestamps, [model_output.peak_ev_load] * len(params.timestamps),
            label='Peak EV Load', color='red', linestyle='--', linewidth=2)

    # Customize the plot
    ax.set_title(f'EV Load Profile - {model_output.model_name}', fontsize=18, weight='bold')
    ax.set_xlabel('Timestamp', fontsize=14)
    ax.set_ylabel('Load (kW)', fontsize=14)

    # Enhance the grid and axes
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=12))  # Minor ticks at 12 PM
    ax.grid(visible=True, which='minor', linestyle='--', linewidth=0.5, alpha=0.6)  # Grid for minor ticks
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.8)  # Grid for major ticks

    # Format x-axis to show day names
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Set major ticks for each day
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))  # Use abbreviated day names ('Mon', 'Tue', etc.)

    # Ensure minor ticks for clarity (optional)
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18, 24]))  # Minor ticks for every 6 hours
    ax.tick_params(axis='x', which='major', labelsize=12)  # Rotate day names for better readability

    # Add a legend outside the plot
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

    # Add top and right borders (spines)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')  # Set color of top border
    ax.spines['right'].set_color('black')  # Set color of right border
    ax.spines['top'].set_linewidth(1)  # Set line width for top border
    ax.spines['right'].set_linewidth(1)  # Set line width for right border

    # Adjust the layout
    fig.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)

    # Save or show the plot
    plt.savefig(f'reports/img/ev_load_plot_{model_output.model_name}.png', dpi=300)  # Save as high-resolution image
    # plt.show()

    # Explicitly close the figure to avoid memory warning
    plt.close(fig)


df = pd.read_csv('../../reports/simulation_results.csv')

# Extract the row where 'Metric' is 'Max charging power (kW)'
max_charging_row = df[df['Metric'] == 'Max charging power (kW)']

# Reshape the row to make all column values into rows
reshaped = max_charging_row.melt(
    id_vars=['Metric'],  # Keep the 'Metric' column
    var_name='Scenario',  # Name for the original column headers
    value_name='Max Charging Power'  # Name for the values
).drop(columns=['Metric'])  # Drop 'Metric' if not needed

# Clean the 'Charging Power (kW)' column by removing the ' kW' part and converting to float
reshaped['Max Charging Power (kW)'] = reshaped['Max Charging Power'].str.replace(' kW', '').astype(float)
reshaped.drop('Max Charging Power', axis=1, inplace=True)
reshaped.set_index('Scenario', inplace=True)


def filter_df(df, model_name: str, tariff_type: str, num_of_evs: int):
    filtered_df = df[
        df.index.str.contains(model_name) & df.index.str.contains(tariff_type) & df.index.str.contains(f'{num_of_evs}EVs')]

    return filtered_df


def plot_p_ev_max(df, tariff_type, num_of_evs):
    # Parse the column names to extract SOC and Distance
    df.loc[:, 'Distance (km)'] = df.index.str.extract(r'(\d+)km')[0].values.astype(int)
    df.loc[:, 'SOC (%)'] = df.index.str.extract(r'SOCmin(\d+)%')[0].values.astype(int)
    print(df)

    # Unique Distance and SOC values
    distance_values = sorted(df['Distance (km)'].unique())  # x-axis
    soc_values = sorted(df['SOC (%)'].unique())  # y-axis

    # Bar width and positions
    x = np.arange(len(distance_values))  # x positions for Distance
    bar_width = 0.2  # Adjust width for multiple bars per group

    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define colors for each SOC
    colours = ['blue', 'orange', 'green', 'red']  # Extend this if needed

    # Plot each SOC as a separate set of bars
    for i, soc in enumerate(soc_values):
        # Filter data for the current SOC
        sub_df = df[df['SOC (%)'] == soc]
        print(f'subdf: {sub_df}')

        # Ensure all distance values are represented
        heights = [
            sub_df[sub_df['Distance (km)'] == distance]['Max Charging Power (kW)'].values[0]
            if distance in sub_df['Distance (km)'].values
            else 0
            for distance in distance_values
        ]
        print(f'heights: {heights}')

        # Plot bars
        ax.bar(x + i * bar_width, heights, bar_width, label=f'{soc}%', color=colours[i % len(colours)])

    # Customize the plot
    # set title
    ax.set_title(f'Optimised CP Capacity - {tariff_type.capitalize()} Tariff - {num_of_evs} EVs', fontsize=16, weight='bold', pad=20)
    ax.text(0.5, 1.02, 'according to average travel distance and minimum SOC', ha='center', va='bottom', fontsize=12,
            transform=ax.transAxes)

    # set labels and ticks
    ax.set_xlabel('Average Travel Distance (km)', fontsize=14)
    ax.set_ylabel('CP Capacity (kW)', fontsize=14)
    ax.set_xticks(x + bar_width * (len(soc_values) - 1) / 2)
    ax.set_xticklabels(distance_values, fontsize=12)

    # Set custom Y-axis ticks to show only unique charging power values
    y_ticks = sorted(df['Max Charging Power (kW)'].unique())  # Unique charging power values
    ax.set_yticks(y_ticks)

    # Set the y-axis label formatting
    ax.set_yticklabels([tick for tick in y_ticks], fontsize=12)

    # Customize the legend
    ax.legend(title='Minimum target SOC', fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=3)

    # Grid configuration
    ax.grid(visible=True, linestyle='--', alpha=0.6, axis='y')

    # Adjust layout
    fig.tight_layout()

    # Save or display the plot
    plt.savefig(f'reports/img/cp_capacity_based_on_soc_and_avg_distance_{tariff_type}_{num_of_evs}EVs.png', dpi=300)
    # plt.show()

mdl_name = 'CS1'
tariff = 'tou'
num_ev = 100

df_clean = filter_df(reshaped, mdl_name, tariff.upper(), num_ev)
print(df_clean)
plot_p_ev_max(df_clean.copy(), tariff, num_ev)