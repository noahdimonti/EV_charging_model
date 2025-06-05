import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from src.config import params


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
    return pd.Series(ranks, index=df.index, name="pareto_rank")


def get_balanced_solution(df: pd.DataFrame):
    # Subset Pareto front with rank 1
    pareto_front = df[df['pareto_rank'] == 1].copy()

    # Compute Euclidean distance to the ideal point (1, 1, 1)
    pareto_front['distance_to_ideal'] = np.sqrt(
        ((1 - pareto_front['investor_score']) ** 2) +
        ((1 - pareto_front['dso_score']) ** 2) +
        ((1 - pareto_front['user_score']) ** 2)
    )

    # Find the index of the most balanced solution (smallest distance)
    best_index = pareto_front['distance_to_ideal'].idxmin()
    best_solution = pareto_front.loc[best_index]

    return best_solution


def parallel_plot_pareto(df: pd.DataFrame, config: str, strategy: str):
    # Rename labels
    rename_dict = {
        'investor_score': 'Investor Score',
        'dso_score': 'DSO Score',
        'user_score': 'User Score'
    }
    df.rename(columns=rename_dict, inplace=True)

    plt.figure(figsize=(15, 5))

    metrics = ['Investor Score', 'DSO Score', 'User Score']

    # Get solutions and pareto rank columns
    parallel_df = df[metrics + ['pareto_rank']].copy()

    # Flip rank values manually for correct colouring
    parallel_df['pareto_rank_flipped'] = parallel_df['pareto_rank'].max() - parallel_df['pareto_rank'] + 1

    conf, num = config.split('_')

    fig_parallel = px.parallel_coordinates(
        parallel_df,
        color='pareto_rank_flipped',  # Use flipped rank for colour mapping
        dimensions=metrics,
        color_continuous_scale=px.colors.diverging.Tealrose[::-1],
        title=f'Parallel Coordinates Plot (Pareto Ranks) - {conf.capitalize()} {num} {strategy.capitalize()}'
    )

    # Correct colorbar labels back to original pareto_rank
    fig_parallel.update_layout(
        coloraxis_colorbar=dict(
            title='Pareto Rank',
            tickvals=parallel_df['pareto_rank_flipped'],
            ticktext=parallel_df['pareto_rank'],  # Show the real rank values
        )
    )

    fig_parallel.write_image(f'{params.project_root}/data/outputs/plots/sensitivity_analysis/pareto_parallel.png', scale=2)
    fig_parallel.show()

