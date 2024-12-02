import pandas as pd
import numpy as np
import warnings

import pyomo.environ as pyo
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from matplotlib.ticker import MaxNLocator
import matplotlib.dates as mdates

from pprint import pprint

import output_collection
import params
import solve_model

from models import uncoordinated_scenario_1 as us1
from models import coordinated_scenario_1 as cs1


# Ignore warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


def print_essential_stats(model_output):
    print(f'--- Essential Statistics ---')
    print(f'Total EV Load: {model_output.total_ev_load} kW')
    print(f'Peak EV Load: {model_output.peak_ev_load} kW')
    print(f'Max charging power: {model_output.max_charging_power} kW')


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
    plt.savefig(f'results_data/img/ev_load_plot_{model_output.model_name}.png', dpi=300)  # Save as high-resolution image
    # plt.show()

    # Explicitly close the figure to avoid memory warning
    plt.close(fig)


def generate_results(
        model_frameworks: dict,
        tariff_types: list[str],
        num_of_evs_list: list[int],
        avg_travel_distance_list: list[float],
        min_soc_list: list[float],
        output_csv_path: str,
        plot: bool = False
):
    """
    Collects results from multiple model runs, compiles them into a single DataFrame,
    and saves the results to a CSV file.

    Parameters:
        model_frameworks (dict): keys: model frameworks to evaluate, values: type of model (coordinated or uncoordinated).
        tariff_types (list[str]): List of tariff types to use in models.
        num_of_evs_list (list[int]): List of EV quantities to test.
        avg_travel_distance_list (list[float]): List of average travel distances (in km).
        min_soc_list (list[float]): List of minimum SOC requirements (as fractions).
        output_csv_path (str): Path to save the resulting CSV file. Default is 'model_results'.
        plot (bool): Whether to plot the results.

    """
    # Create a list to store DataFrame results from all model runs
    all_model_dfs = []

    # Dictionary to store P_EV_max from coordinated models
    p_ev_max_dict = {}

    # Iterate through each combination of inputs
    for model_framework, model_type in model_frameworks.items():
        for tariff_type in tariff_types:
            for num_of_evs in num_of_evs_list:
                for avg_travel_distance in avg_travel_distance_list:
                    for min_soc in min_soc_list:
                        # Generate and solve the model instance
                        try:
                            # Create model_instance variable
                            model_instance = None

                            if model_type == 'coordinated':
                                # Create and solve coordinated model
                                model_instance = model_framework.create_optimisation_model_instance(
                                    tariff_type, num_of_evs, avg_travel_distance, min_soc
                                )
                                solve_model.solve_optimisation_model(model_instance)

                                # Store P_EV_max for later use
                                p_ev_max = pyo.value(model_instance.P_EV_max) * params.P_EV_resolution_factor
                                p_ev_max_dict[(tariff_type, num_of_evs, avg_travel_distance, min_soc)] = p_ev_max

                            elif model_type == 'uncoordinated':
                                # Retrieve P_EV_max from the coordinated model
                                if (tariff_type, num_of_evs, avg_travel_distance, min_soc) not in p_ev_max_dict:
                                    raise ValueError(
                                        f'P_EV_max is not available for coordinated model with parameters:\n'
                                        f'tariff_type={tariff_type}, num_of_evs={num_of_evs}, '
                                        f'avg_travel_distance={avg_travel_distance}, min_soc={min_soc}')

                                p_ev_max = p_ev_max_dict[(tariff_type, num_of_evs, avg_travel_distance, min_soc)]

                                # Create and simulate the uncoordinated model
                                model_instance = model_framework.simulate_uncoordinated_model(
                                    p_ev_max, tariff_type, num_of_evs, avg_travel_distance, min_soc
                                )
                                solve_model.simulate_uncoordinated_model(model_instance)

                            # Collect outputs and convert them to a DataFrame
                            model_output = output_collection.collect_model_outputs(
                                model_instance, model_type, tariff_type, num_of_evs, avg_travel_distance, min_soc
                            )

                            # print essential statistics and plot results
                            print_essential_stats(model_output)

                            # plot the output
                            if plot:
                                plot_results(model_output)

                            # Convert model_output object into a dataframe
                            output_df = model_output.to_dataframe()

                            # Append DataFrame to the list
                            all_model_dfs.append(output_df)

                        except ValueError as e:
                            print(f'Error processing {model_type} model with parameters:\n'
                                  f'tariff_type={tariff_type}, num_of_evs={num_of_evs}, '
                                  f'avg_travel_distance={avg_travel_distance}, min_soc={min_soc}.\n'
                                  f'Error detail: {e}')

    # Combine all DataFrames horizontally (axis=1)
    combined_df = pd.concat(all_model_dfs, axis=1)

    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_csv_path, index=True)
    print(f'---------------------------------------------------------\n')
    print(f'{params.GREEN}Simulation is completed.{params.RESET}')
    print(f'Results saved to {output_csv_path}\n')
    print(f'---------------------------------------------------------\n')

    return combined_df


# Model variables
models = {
    cs1: 'coordinated',
    us1: 'uncoordinated'
}
tariffs = [
    'flat',
    'tou'
]
num_evs = [
    50,
    100
]
avg_dist = [
    15,
    25,
    35
]
min_soc = [
    0.4,
    0.6,
    0.8
]

# # Generate and print results
# df = generate_results(models, tariffs, num_evs, avg_dist, min_soc, output_csv_path=f'results_data/simulation_results.csv')
# print(df)



df = pd.read_csv('results_data/simulation_results.csv')

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
    plt.savefig(f'results_data/img/cp_capacity_based_on_soc_and_avg_distance_{tariff_type}_{num_of_evs}EVs.png', dpi=300)
    # plt.show()

mdl_name = 'CS1'
tariff = 'tou'
num_ev = 100

df_clean = filter_df(reshaped, mdl_name, tariff.upper(), num_ev)
print(df_clean)
plot_p_ev_max(df_clean.copy(), tariff, num_ev)