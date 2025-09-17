import pandas as pd
import pickle
import os

from pprint import pprint

from src.config import params
from src.pipelines.augmecon.process_pareto_solutions import get_pareto_solutions


def main():
    versions = [
        {'config': 'config_1', 'strategy': 'opportunistic', 'grid_points': 20},
        {'config': 'config_1', 'strategy': 'flexible', 'grid_points': 20},
        {'config': 'config_2', 'strategy': 'opportunistic', 'grid_points': 20},
        {'config': 'config_2', 'strategy': 'flexible', 'grid_points': 10},
        {'config': 'config_3', 'strategy': 'opportunistic', 'grid_points': 20},
        {'config': 'config_3', 'strategy': 'flexible', 'grid_points': 8},
    ]

    augmecon_results = []

    for version in versions:
        config = version['config']
        strategy = version['strategy']
        grid_points = version['grid_points']

        df = get_pareto_solutions(
            config,
            strategy,
            grid_points
        )

        # Best solutions (lowest distance to ideal)
        best_sol = df[df['distance_to_ideal'] == df['distance_to_ideal'].min()].head(1)
        best_sol_version = best_sol['version'].values

        augmecon_results.append({
            'model': f'{config}_{strategy}',
            'best_solution': best_sol_version.item()
        })

    pprint(augmecon_results)

    # Save best solution with a uniform version name
    for result in augmecon_results:
        model_name = result['model']
        version = result['best_solution']
        filename = f'{model_name}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
        filepath = os.path.join(params.model_results_folder_path, filename)

        if os.path.exists(filepath):
            # Load best solution pkl file
            with open(filepath, 'rb') as f:
                data = pickle.load(f)

            # Dump best solution as pkl file with a new name version
            new_filename = f'{model_name}_{params.num_of_evs}EVs_{params.num_of_days}days_augmecon.pkl'
            new_filepath = os.path.join(params.model_results_folder_path, new_filename)
            with open(new_filepath, 'wb') as f:
                pickle.dump(data, f)

        else:
            raise FileNotFoundError(f'File path does not exist:\n{filepath}')


if __name__ == '__main__':
    main()