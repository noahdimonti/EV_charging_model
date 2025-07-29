import pandas as pd
import ast  # To safely parse string to dictionary
import os
from src.config import params
from pprint import pprint


# Load the CSV
filename = 'data/outputs/epsilon_constraint/epsilon_bounds.csv'
filepath = os.path.join(params.project_root, filename)
df = pd.read_csv(filepath, index_col=0)
df = df[['economic_active', 'technical_active', 'social_active']]
print(df)

# Parse stringified dictionaries
for col in df.columns:
    df[col] = df[col].apply(ast.literal_eval)

print(df.loc['config_1_opportunistic', 'economic_active']['economic_objective']
)


objectives = ['economic_objective', 'technical_objective', 'social_objective']
components = ['economic_active', 'technical_active', 'social_active']

epsilon_bounds = {}

for obj in objectives:
    epsilon_bounds[obj] = {'min': float('inf'), 'max': float('-inf')}

    for col in components:
        for val in df[col]:
            v = val[obj]
            if v < epsilon_bounds[obj]['min']:
                epsilon_bounds[obj]['min'] = v
            if v > epsilon_bounds[obj]['max']:
                epsilon_bounds[obj]['max'] = v


pprint(epsilon_bounds)
