import os
import pickle
from pprint import pprint
from src.config import params


version = 'prelim_results'
file = f'config_3_opportunistic_10EVs_7days_{version}.pkl'
file_path = os.path.join(params.model_results_folder_path, file)

with open(file_path, 'rb') as f:
    data = pickle.load(f)

print(data.variables.keys())
print(data.variables['num_cp'])

print('ev_is_permanently_assigned_to_cp')
pprint(data.variables['ev_is_permanently_assigned_to_cp'])

print('cp_is_installed')
pprint(data.variables['cp_is_installed'])

print('num_ev_sharing_cp')
pprint(data.variables['num_ev_sharing_cp'])

