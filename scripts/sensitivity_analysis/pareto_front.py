import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

from scripts.sensitivity_analysis.sensitivity_analysis_tools import get_holistic_metrics
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

    # Get the minimum distance
    min_distance = pareto_front['distance_to_ideal'].min()

    # Find all rows with that minimum distance
    best_solutions = pareto_front[np.isclose(pareto_front['distance_to_ideal'], min_distance, atol=1e-8)]

    return best_solutions


def get_pareto_results(
        config: str,
        strategy: str,
        step: float,
        sens_analysis_res: pd.DataFrame = None) -> pd.DataFrame:
    # Get raw data from sensitivity analysis file
    if sens_analysis_res is None:
        sens_filename = (f'sensitivity_analysis_'
                         f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{step}step.csv')
        file_path = os.path.join(params.sensitivity_analysis_res_path, sens_filename)
        df = pd.read_csv(file_path)
    else:
        df = sens_analysis_res

    # Convert raw data into holistic metrics
    holistic_metrics = get_holistic_metrics(df)

    # Get solution columns and pareto ranks
    solutions = holistic_metrics[['investor_score', 'dso_score', 'user_score']]
    ranks = get_pareto_ranks(solutions)

    # Append pareto ranks to holistic metrics dataframe
    holistic_with_pareto_ranks = holistic_metrics.assign(pareto_rank=ranks).sort_values('pareto_rank')

    # Save pareto front rank data to csv
    holistic_pareto_filename = (f'holistic_metrics_pareto_front_'
                                f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{step}step.csv')
    holistic_pareto_filepath = os.path.join(params.sensitivity_analysis_res_path, holistic_pareto_filename)

    holistic_with_pareto_ranks.to_csv(holistic_pareto_filepath)
    print(f'\nHolistic metrics with pareto rank saved to:\n{holistic_pareto_filepath}')

    best_solution = get_balanced_solution(holistic_with_pareto_ranks)
    print(f'\nBest solution(s):\n{best_solution}')

    return holistic_with_pareto_ranks


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

    filename = f'pareto_parallel_{config}_{strategy}_{params.num_of_evs}EVs.png'
    filepath = os.path.join(params.plots_folder_path, 'sensitivity_analysis', filename)
    fig_parallel.write_image(filepath, scale=2)
    fig_parallel.show()

