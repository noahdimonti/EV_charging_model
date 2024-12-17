import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.data import create_ev_data

num_ev = 100
avg_distance = 25
min_soc = 0.5

ev_data = create_ev_data.main(num_ev, avg_distance, min_soc)

df = pd.concat([ev.at_home_status for ev in ev_data], axis=1)
df_sum = df.sum(axis=1)



# Function to calculate durations of consecutive 1s
def calculate_durations(series, resolution_minutes=15):
    durations = []
    current_duration = 0
    for value in series:
        if value == 1:
            current_duration += resolution_minutes
        elif current_duration > 0:
            durations.append(current_duration)
            current_duration = 0
    if current_duration > 0:  # Capture any remaining duration
        durations.append(current_duration)
    return durations


# Calculate durations for all EVs
all_durations = []
for col in df.columns:
    all_durations.extend(calculate_durations(df[col]))

# Convert durations to hours
all_durations_hours = [duration / 60 for duration in all_durations]


# Plot the distribution
def plot_durations_distribution(duration):
    plt.figure(figsize=(10, 6))
    plt.hist(duration, bins=np.arange(0, max(duration) + 0.25, 0.25), color='skyblue', edgecolor='black', alpha=0.8)
    plt.title('Distribution of Duration EVs Are at Home between Departure Times', fontsize=16, weight='bold')
    plt.xlabel('Duration at Home (hours)', fontsize=14)
    plt.ylabel('Frequency', fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.savefig('/Users/noahdimonti/Developer/PycharmProjects/EV_apartment_model/reports/figures/durations_at_home_distribution.png', dpi=300)
    plt.show()



def plot_tou_tariff(timestamps, tou_tariff):
    plt.style.use('default')

    fig, ax = plt.subplots(figsize=(12, 8))  # Adjust size for presentation

    # Plot TOU tariff
    ax.plot(timestamps, tou_tariff, label='TOU Tariff (Rate)', color='green', linewidth=2)

    # Customize the plot
    ax.set_title('Time-of-Use Tariff', fontsize=18, weight='bold')
    ax.set_xlabel('Timestamp', fontsize=14)
    ax.set_ylabel('Tariff Rate ($/kWh)', fontsize=14)

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

    # Add top and right borders (spines)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')  # Set color of top border
    ax.spines['right'].set_color('black')  # Set color of right border
    ax.spines['top'].set_linewidth(1)  # Set line width for top border
    ax.spines['right'].set_linewidth(1)  # Set line width for right border

    # Adjust the layout
    fig.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)

    # Save and show
    plt.savefig('/Users/noahdimonti/Developer/PycharmProjects/EV_apartment_model/reports/figures/tou_tariff_plot.png', dpi=300)
    plt.show()

    # Close the figure
    plt.close(fig)



def plot_arrival_departure_distribution(departure_times, arrival_times):
    # Convert to hours
    departure_hours = [t.hour + t.minute / 60 for t in departure_times]
    arrival_hours = [t.hour + t.minute / 60 for t in arrival_times]

    # Create bins for 24 hours
    bins = np.arange(0, 25, 1)  # 0 to 24 inclusive
    departure_hist, _ = np.histogram(departure_hours, bins=bins)
    arrival_hist, _ = np.histogram(arrival_hours, bins=bins)

    # Offset for side-by-side bars
    bar_width = 0.4
    x_ticks = bins[:-1]  # Use bin start times as x-ticks

    # Plotting
    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot departure bars
    ax.bar(x_ticks + bar_width / 2, departure_hist, width=bar_width, color='blue', alpha=0.7, label='Departures')

    # Plot arrival bars
    ax.bar(x_ticks - bar_width / 2, arrival_hist, width=bar_width, color='orange', alpha=0.7, label='Arrivals')

    # Formatting
    ax.set_title('Departure and Arrival Time Distribution', fontsize=18, weight='bold')
    ax.set_xlabel('Hour of Day', fontsize=14)
    ax.set_ylabel('Count', fontsize=14)
    ax.set_xticks(bins[:-1])  # Align labels with each hour
    ax.set_xticklabels([f'{int(hour)}:00' for hour in x_ticks], rotation=45)

    # Ensure symmetry of the x-axis by extending limits
    ax.set_xlim(-0.5, 24.5)  # Start slightly before 0 and extend slightly after 24

    # Add grid
    ax.grid(visible=True, linestyle='--', alpha=0.5, axis='y')

    # Add legend at the bottom
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)

    # Adjust layout
    plt.tight_layout(rect=[0, 0.1, 1, 1])  # Leave space for the legend below

    # Save and show
    plt.tight_layout()
    plt.savefig('/Users/noahdimonti/Developer/PycharmProjects/EV_apartment_model/reports/figures/arrival_departure_distribution.png', dpi=300)
    plt.show()


dep_times_list = []
arr_times_list = []
for ev in ev_data:
    dep_times_list.extend(ev.t_dep)
    arr_times_list.extend(ev.t_arr)



plot_durations_distribution(all_durations_hours)
plot_tou_tariff(params.timestamps, params.create_tou_tariff(params.timestamps))
plot_arrival_departure_distribution(dep_times_list, arr_times_list)
