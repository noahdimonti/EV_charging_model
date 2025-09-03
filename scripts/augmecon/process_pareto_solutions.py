import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from src.config import params
from src.utils.argparser import get_parser
from pprint import pprint


def get_pareto_solutions(config, charging_strategy, grid_points):
    # Load CSV
    filepath = os.path.join(
        params.data_output_path,
        f'augmecon/pareto_{config}_{charging_strategy}_{params.num_of_evs}EVs_social_primary_{grid_points}gp.csv'
    )
    df = pd.read_csv(filepath)

    # Compute ranks
    objective_cols = ['social', 'economic', 'technical']
    df['pareto_rank'] = get_pareto_ranks_min(df[objective_cols])

    # Get distance to ideal
    df = get_distance_to_ideal_min(df, objective_cols)

    # Sort by Pareto rank first, then by distance to ideal
    df = df.sort_values(['pareto_rank', 'distance_to_ideal']).reset_index(drop=True)

    return df


def get_pareto_ranks_min(df: pd.DataFrame) -> pd.Series:
    """
    Assign Pareto ranks to each solution in the DataFrame.

    Parameters:
    - df: A DataFrame where each row is a solution and each column is a normalised objective (higher is better).

    Returns:
    - A Series containing the Pareto rank for each row (1 = best Pareto front).
    """
    num_points = df.shape[0]

    # Initialise an array to store the rank of each point
    ranks = np.zeros(num_points, dtype=int)

    # Tracks which solutions have not been ranked yet
    remaining = set(range(num_points))

    # Start with Pareto rank 1 (the best front)
    current_rank = 1

    # Repeat until all points are ranked
    while remaining:
        current_front = set()

        # Identify the current Pareto front from the remaining solutions
        for i in remaining:
            dominated = False
            for j in remaining:
                if i == j:
                    continue

                # Check if solution j dominates solution i (for minimisation)
                dominates = (df.iloc[j] <= df.iloc[i]).all() and (df.iloc[j] < df.iloc[i]).any()
                if dominates:
                    dominated = True
                    break  # No need to check further; i is dominated

            if not dominated:
                current_front.add(i)

        # Assign current Pareto rank to all solutions in the front
        for idx in current_front:
            ranks[idx] = current_rank

        # Remove the ranked solutions from the remaining set
        remaining -= current_front

        # Increment the rank for the next front
        current_rank += 1

    # Return the ranks as a Series with the same index as the original DataFrame
    return pd.Series(ranks, index=df.index, name='pareto_rank')



def get_distance_to_ideal_min(df: pd.DataFrame, objectives: list) -> pd.DataFrame:
    # Ideal point = minimum for each objective
    ideal_point = df[objectives].min()

    # Calculate squared differences for each objective
    sq_diff = (df[objectives] - ideal_point) ** 2

    # Sum across objectives (axis=1) and take square root
    df = df.copy()
    df['distance_to_ideal'] = np.sqrt(sq_diff.sum(axis=1))

    return df.sort_values('distance_to_ideal')


if __name__ == '__main__':
    main(
        [
            '-c', 'config_2',
            '-s', 'flexible',
            '-g', '10'
        ]
    )