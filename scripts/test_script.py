import os
import pickle
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
from pprint import pprint
from src.config import params
from scripts.experiments_pipeline import run_pipeline



# Script actions
run = False
# run = True


# Run model
if run:
    run_pipeline.main()


config = 'config_3'
version = 'run_test'
num_ev = params.num_of_evs
file = f'{config}_opportunistic_{num_ev}EVs_7days_{version}.pkl'
file_path = os.path.join(params.model_results_folder_path, file)
print(f'File path: {file_path}')


with open(file_path, 'rb') as f:
    data = pickle.load(f)

print(f'Variable keys: {data.variables.keys()}')