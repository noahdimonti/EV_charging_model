import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Example EV charging schedule (EV ID, Day, Start Hour, End Hour)
charging_schedule = [
    ('EV 1', 'Monday', 8, 12),
    ('EV 2', 'Monday', 10, 14),
    ('EV 3', 'Tuesday', 9, 13),
    ('EV 1', 'Wednesday', 14, 18),
    ('EV 2', 'Wednesday', 12, 16),
    ('EV 3', 'Friday', 8, 11)
]

# Convert to DataFrame
df = pd.DataFrame(charging_schedule, columns=['EV', 'Day', 'Start', 'End'])

# Sort days for consistent plotting order
day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
df['Day'] = pd.Categorical(df['Day'], categories=day_order, ordered=True)
df.sort_values(['Day', 'Start'], inplace=True)

# Create figure and axes
fig, ax = plt.subplots(figsize=(10, 6))

# Assign unique colors to each EV
ev_colors = {ev: color for ev, color in zip(df['EV'].unique(), plt.cm.Set2.colors)}

# Track the bottom position for stacking
bottom = {day: 0 for day in day_order}

# Plot stacked bars for each EV
for row in df.itertuples():
    duration = row.End - row.Start
    ax.bar(row.Day, duration, bottom=bottom[row.Day], color=ev_colors[row.EV], label=row.EV)
    bottom[row.Day] += duration

# Formatting the chart
ax.set_ylabel("Charging Duration (Hours)")
ax.set_xlabel("Days of the Week")
ax.set_title("EV Charging Schedule (Flexible Days)")
ax.legend(title="EVs", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(axis='y', linestyle='--', linewidth=0.5)

plt.tight_layout()
plt.show()
