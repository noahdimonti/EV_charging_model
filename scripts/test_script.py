import os
import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyomo.environ as pyo
from collections import defaultdict
from pprint import pprint
from src.config import params
from scripts.experiments_pipeline import run_pipeline


# Script actions
# run = False
run = True
test = True


# Run model
if run:
    run_pipeline.main()

# before refactor
# Model fingerprint: 0x58c222a1
# Model has 4 quadratic objective terms
# Model has 67872 quadratic constraints
# Variable types: 74594 continuous, 60595 integer (60583 binary)

# Presolved model has 1 bilinear constraint(s)
#
# Solving non-convex MIQCP
#
# Variable types: 86457 continuous, 41014 integer (40999 binary)


# Installed CPs: [0, 5]
# Num of EVs per CP
# CP 0: 5 EVs
# CP 5: 5 EVs
# EV Assignment to CP
# {0: [0, 1, 3, 5, 6], 5: [2, 4, 7, 8, 9]}
# CP 0: EV [0, 1, 3, 5, 6]
# CP 5: EV [2, 4, 7, 8, 9]



# refactored
# Model fingerprint: 0x4e87be29
# Model has 4 quadratic objective terms
# Model has 67200 quadratic constraints
# Variable types: 74594 continuous, 60595 integer (60583 binary)



version = 'test_conf3_bug'
num_ev = params.num_of_evs
file = f'config_3_opportunistic_{num_ev}EVs_7days_{version}.pkl'
file_path = os.path.join(params.model_results_folder_path, file)
print(file_path)


with open(file_path, 'rb') as f:
    data = pickle.load(f)

print(data.variables.keys())
print(f'p_cp_total: {data.variables['p_cp_total']}')
print(f'p_cp_rated: {data.variables['p_cp_rated']}')

print('\n')
print(f'num ev: {num_ev}')
print(f'num cp: {int(data.variables['num_cp'])}')

print('is_ev_permanently_assigned_to_cp')
print('(ev_id, cp_id)')
ev_is_permanently_assigned_to_cp = data.variables['is_ev_permanently_assigned_to_cp']
pprint(ev_is_permanently_assigned_to_cp)

# print('cp_is_installed')
cp_is_installed = data.variables['is_cp_installed']
# pprint(cp_is_installed)

# print('num_ev_per_cp')
num_ev_per_cp = data.variables['num_ev_per_cp']
# pprint(num_ev_per_cp)

p_ev = data.variables['p_ev']
soc_ev = data.variables['soc_ev']

ev_is_connected_to_cp_j = data.variables['is_ev_cp_connected']


if test:
    # Print installed CPs
    installed_cps = []
    for cp, installed in cp_is_installed.items():
        if installed == 1:
            installed_cps.append(cp)
    print(f'Installed CPs: {[cp for cp in installed_cps]}')

    # Print number of EVs per CP
    num_ev_per_cp_j = defaultdict(int)
    for cp, evs in num_ev_per_cp.items():
        if evs > 0:
            num_ev_per_cp_j[cp] = int(evs)
    print('Num of EVs per CP')
    for cp_id, num_ev_in_cp in num_ev_per_cp.items():
        if cp_id in installed_cps:
            print(f'CP {cp_id}: {int(num_ev_in_cp)} EVs')

    # 1. Build a reverse map: cp_id -> list of ev_ids assigned
    cp_to_evs = defaultdict(list)
    for (ev_id, cp_id), assigned in ev_is_permanently_assigned_to_cp.items():
        if assigned == 1.0:
            cp_to_evs[cp_id].append(ev_id)
    sorted_cp_to_evs = dict(sorted(cp_to_evs.items()))
    print('EV Assignment to CP')
    pprint(sorted_cp_to_evs)
    for cp_id, ev_list in sorted_cp_to_evs.items():
        print(f'CP {cp_id}: EV {ev_list}')

    # 2. For each timestamp, check CP-level total active charging EVs
    timestamp_cp_loads = defaultdict(lambda: defaultdict(int))  # timestamp -> cp -> active_ev_count



    for (ev_id, timestamp), power in p_ev.items():
        if power > 0:
            try:
                assigned_cp = next(cp for (e, cp), assigned in ev_is_permanently_assigned_to_cp.items()
                                   if e == ev_id and assigned == 1.0)
                timestamp_cp_loads[timestamp][assigned_cp] += 1
            except StopIteration:
                print(f"⚠️ No CP assignment found for EV {ev_id} at time {timestamp} despite power > 0")


    # 3. Raise error if any CP has more than 1 EV charging at once
    for timestamp, cp_counts in timestamp_cp_loads.items():
        for cp_id, count in cp_counts.items():
            if count > 1:
                print(f"❌ Overlap at time {timestamp} on CP {cp_id}: {count} EVs charging!")


    # Check that each EV is assigned to exactly one CP
    for ev_id in range(num_ev):
        assigned_cps = [cp_id for (e, cp_id), assigned in ev_is_permanently_assigned_to_cp.items() if e == ev_id and assigned == 1.0]
        if len(assigned_cps) != 1:
            print(f"❌ EV {ev_id} is assigned to {len(assigned_cps)} CPs: {assigned_cps}")


    # Confirm that assigned CPs are installed
    for (ev_id, cp_id), assigned in ev_is_permanently_assigned_to_cp.items():
        if assigned == 1.0 and cp_is_installed[cp_id] != 1.0:
            print(f"❌ EV {ev_id} assigned to CP {cp_id}, which is not installed!")


    for cp_id in range(len(cp_is_installed)):
        assigned_evs = cp_to_evs[cp_id]
        if len(assigned_evs) != num_ev_per_cp[cp_id]:
            print(f"❌ Mismatch on CP {cp_id}: assigned {len(assigned_evs)}, expected {num_ev_per_cp[cp_id]}")


    for j in data.sets['CP_ID']:
        for t in data.sets['TIME']:
            evs_connected = [i for i in data.sets['EV_ID'] if pyo.value(ev_is_connected_to_cp_j[i, j, t]) > 0.5]
            if len(evs_connected) > 1:
                print(f"More than one EV connected at CP {j} at time {t}: EVs {evs_connected}")

    evs_connected = [i for i in data.sets['EV_ID'] if pyo.value(ev_is_connected_to_cp_j[i, j, t]) > 0.5]





def print_log(cp_id, timestamp):

    print(f'\nCP_ID {cp_id}, Timestamp: {timestamp}\n')

    for ev in data.sets['EV_ID']:
        print(f'EV {ev} is connected to CP {cp_id}: {'Yes' if (ev_is_connected_to_cp_j[ev, cp_id, pd.Timestamp(timestamp)]) else 'No'},'
              f' p_ev: {p_ev[ev, pd.Timestamp(timestamp)]}, p_ev_cp: {data.variables['p_ev_cp'][ev, cp_id, pd.Timestamp(timestamp)]}')

    print('\n')


for cp in installed_cps:
    print_log(cp, '2022-02-24 22:45:00')








p_ev_cp = data.variables['p_ev_cp']  # dict with (i, j, timestamp)

# Extract unique sorted values
ev_indices = sorted({k[0] for k in p_ev_cp})
cp_indices = sorted({k[1] for k in p_ev_cp})
timestamps = sorted({k[2] for k in p_ev_cp})  # pandas Timestamps

num_evs = max(ev_indices) + 1
num_cps = max(cp_indices) + 1
num_timesteps = len(timestamps)

# Map timestamps to indices
timestamp_to_index = {t: idx for idx, t in enumerate(timestamps)}

# Create empty array
p_ev_cp_array = np.zeros((num_evs, num_cps, num_timesteps))

# Fill the array
for (i, j, t), val in p_ev_cp.items():
    t_idx = timestamp_to_index[t]
    p_ev_cp_array[i, j, t_idx] = val

assigned_cp = -1 * np.ones((num_evs, num_timesteps), dtype=int)
threshold = 1e-3  # filter numerical noise

for i in range(num_evs):
    for t in range(num_timesteps):
        cp_charging = np.where(p_ev_cp_array[i, :, t] > threshold)[0]
        if len(cp_charging) == 1:
            assigned_cp[i, t] = cp_charging[0]
        elif len(cp_charging) > 1:
            print(f"⚠️ EV {i} is charging from multiple CPs at time {timestamps[t]}: {cp_charging}")


# import matplotlib.colors as mcolors
#
# # Use only installed CPs
# installed_cps = sorted({cp for (_, cp, _) in p_ev_cp if data.variables['is_cp_installed'][cp] == 1})
# cp_index_map = {cp: i for i, cp in enumerate(installed_cps)}
# num_cps_installed = len(installed_cps)
#
# # Build the assignment array (EVs x Time)
# assigned_cp = np.full((num_evs, len(timestamps)), -1)  # -1 = not connected
#
# # Create a mapping from timestamp -> index
# timestamp_to_index = {ts: i for i, ts in enumerate(timestamps)}
#
# for (ev, cp, t), p in p_ev_cp.items():
#     if isinstance(t, pd.Timestamp):
#         t_index = timestamp_to_index[t]
#     else:
#         t_index = t  # assume it's already an int if not a timestamp
#
#     if data.variables['is_cp_installed'][cp] == 1 and p > 0:
#         assigned_cp[int(ev), t_index] = cp_index_map[cp]
#
#
# # Create a colormap that handles -1 as background
# cmap = plt.cm.get_cmap('tab20', num_cps_installed)
# colors = cmap(np.arange(num_cps_installed))
# colors = np.vstack(([0.9, 0.9, 0.9, 1.0], colors))  # Add gray for -1
# new_cmap = mcolors.ListedColormap(colors)
# bounds = np.arange(-1.5, num_cps_installed + 0.5, 1)
# norm = mcolors.BoundaryNorm(bounds, new_cmap.N)
#
# # Plotting
# plt.figure(figsize=(15, 6))
# im = plt.imshow(
#     assigned_cp,
#     aspect='auto',
#     cmap=new_cmap,
#     norm=norm,
#     interpolation='nearest'
# )
# cbar = plt.colorbar(im, ticks=np.arange(0, num_cps_installed))
# cbar.set_label('CP index (installed only)')
# cbar.set_ticklabels([f'CP {cp}' for cp in installed_cps])
#
# # X-axis: every 6 hours
# six_hour_indices = [i for i, ts in enumerate(timestamps) if ts.hour % 6 == 0 and ts.minute == 0]
# plt.xticks(
#     ticks=six_hour_indices,
#     labels=[timestamps[i].strftime('%Y-%m-%d %H:%M') for i in six_hour_indices],
#     rotation=45
# )
#
# # Y-axis: one tick per EV
# plt.yticks(
#     ticks=np.arange(num_evs),
#     labels=[f'EV {i}' for i in range(num_evs)]
# )
#
# # Add grid lines
# for y in range(num_evs):
#     plt.axhline(y - 0.5, color='lightgray', linewidth=0.5)
# for x in six_hour_indices:
#     plt.axvline(x - 0.5, color='lightgray', linewidth=0.5)
#
# plt.xlabel("Time")
# plt.ylabel("EV index")
# plt.title("EV–CP assignment over time (installed CPs only)")
# plt.tight_layout()
#
#
# plt.savefig('ev_cp.png')
# plt.show()


# First timestamp's date
first_day = pd.Timestamp(timestamps[0]).normalize()

# Get indices where the timestamp falls on the first day
first_day_indices = [i for i, ts in enumerate(timestamps) if pd.Timestamp(ts).normalize() == first_day]

# Slice assigned_cp for first day
assigned_cp_day1 = assigned_cp[:, first_day_indices]
timestamps_day1 = [timestamps[i] for i in first_day_indices]

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(12, 6))

# Show EV-CP assignments
cmap = plt.get_cmap('tab10', len(installed_cps) + 1)
im = ax.imshow(
    assigned_cp_day1,
    aspect='auto',
    interpolation='nearest',
    cmap=cmap,
    vmin=-1,
    vmax=len(installed_cps) - 1
)

# Y-axis: one tick per EV
ax.set_ylabel("EV Index")
ax.set_yticks(np.arange(num_evs))

# X-axis: label every 6 hours = 24 intervals at 15-min resolution
x_ticks = np.arange(0, len(timestamps_day1), 24)
x_labels = [timestamps_day1[i].strftime('%H:%M') for i in x_ticks]
ax.set_xticks(x_ticks)
ax.set_xticklabels(x_labels, rotation=45)
ax.set_xlabel("Time")

# Grids
ax.grid(axis='x', linestyle='--', color='gray', linewidth=0.5)
ax.set_yticks(np.arange(num_evs), minor=True)
ax.grid(axis='y', which='minor', linestyle=':', color='gray', linewidth=0.5)

# Colorbar
cbar = plt.colorbar(im, ax=ax, ticks=np.arange(-1, len(installed_cps)))
cbar.set_label("Assigned CP Index (-1 = Not Connected)")
cbar.ax.set_yticklabels(['None'] + [str(i) for i in installed_cps])

plt.title("EV–CP Assignments (First Day Only)")
plt.tight_layout()
# plt.savefig('ev_cp one day.png')
# plt.show()
