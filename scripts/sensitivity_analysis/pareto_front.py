import os
import pandas as pd
import numpy as np


def is_dominated(row, others):
    # A row is dominated if there's *any* other row that is >= in all objectives and > in at least one
    for _, other in others.iterrows():
        if (other >= row).all() and (other > row).any():
            return True

    return False


def get_pareto_front_indices(df):
    front_indices = []
    for i, row in df.iterrows():
        # Create df of `other` rows
        others = df.drop(index=i)

        # Append row index if row is non-dominated
        if not is_dominated(row, others):
            front_indices.append(i)

    return front_indices


def get_pareto_ranks(df: pd.DataFrame) -> pd.Series:
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

                # Check if solution j dominates solution i
                dominates = (df.iloc[j] >= df.iloc[i]).all() and (df.iloc[j] > df.iloc[i]).any()
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


