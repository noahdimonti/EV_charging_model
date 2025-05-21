import os
import pickle
import matplotlib.pyplot as plt
import pandas as pd
import pyomo.environ as pyo
from collections import defaultdict
from pprint import pprint
from src.config import params


version = 'test_conf3_bug'
num_ev = params.num_of_evs
file = f'config_3_opportunistic_{num_ev}EVs_7days_{version}.pkl'
file_path = os.path.join(params.model_results_folder_path, file)
print(file_path)

with open(file_path, 'rb') as f:
    data = pickle.load(f)

print(data.variables.keys())
print(f'num ev: {num_ev}')
print(f'num cp: {data.variables['num_cp']}')

print('ev_is_permanently_assigned_to_cp')
print('(ev_id, cp_id)')
ev_is_permanently_assigned_to_cp = data.variables['ev_is_permanently_assigned_to_cp']
pprint(ev_is_permanently_assigned_to_cp)

print('cp_is_installed')
cp_is_installed = data.variables['cp_is_installed']
pprint(cp_is_installed)

print('num_ev_sharing_cp')
num_ev_sharing_cp = data.variables['num_ev_sharing_cp']
pprint(num_ev_sharing_cp)

p_ev = data.variables['p_ev']
soc_ev = data.variables['soc_ev']

ev_is_connected_to_cp_j = data.variables['ev_is_connected_to_cp_j']

# pprint(f'p_ev: {p_ev}')
# pprint(f'soc_ev: {soc_ev}')



# 1. Build a reverse map: cp_id -> list of ev_ids assigned
cp_to_evs = defaultdict(list)
for (ev_id, cp_id), assigned in ev_is_permanently_assigned_to_cp.items():
    if assigned == 1.0:
        cp_to_evs[cp_id].append(ev_id)

# 2. For each timestamp, check CP-level total active charging EVs
timestamp_cp_loads = defaultdict(lambda: defaultdict(int))  # timestamp -> cp -> active_ev_count
print(timestamp_cp_loads)

for (ev_id, timestamp), power in p_ev.items():
    if power > 0:
        # Find which cp this ev is assigned to
        assigned_cp = next(cp for (e, cp), assigned in ev_is_permanently_assigned_to_cp.items()
                           if e == ev_id and assigned == 1.0)
        timestamp_cp_loads[timestamp][assigned_cp] += 1

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
    if len(assigned_evs) != num_ev_sharing_cp[cp_id]:
        print(f"❌ Mismatch on CP {cp_id}: assigned {len(assigned_evs)}, expected {num_ev_sharing_cp[cp_id]}")


for j in data.sets['CP_ID']:
    for t in data.sets['TIME']:
        evs_connected = [i for i in data.sets['EV_ID'] if pyo.value(ev_is_connected_to_cp_j[i, j, t]) > 0.5]
        if len(evs_connected) > 1:
            print(f"More than one EV connected at CP {j} at time {t}: EVs {evs_connected}")

evs_connected = [i for i in data.sets['EV_ID'] if pyo.value(ev_is_connected_to_cp_j[i, j, t]) > 0.5]

timestmp = '2022-02-24 17:30:00'
for ev in data.sets['EV_ID']:
    print(f'ev id: {ev}')
    print(ev_is_connected_to_cp_j[ev, 4, pd.Timestamp(timestmp)])
print()
for ev in data.sets['EV_ID']:
    print(f'ev id: {ev}')
    print(p_ev[ev, pd.Timestamp(timestmp)])







