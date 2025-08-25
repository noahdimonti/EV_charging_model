import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from src.config import params
from src.utils.argparser import get_parser
from pprint import pprint


def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(argv)

    # Load CSV
    filepath = os.path.join(
        params.data_output_path,
        f'augmecon/pareto_{args.config}_{args.charging_strategy}_{params.num_of_evs}EVs_social_primary_{args.grid_points}gp.csv'
    )
    df = pd.read_csv(filepath)

    # Compute ranks
    objective_cols = ['social', 'economic', 'technical']
    df['pareto_rank'] = get_pareto_ranks_min(df[objective_cols])

    # Get distance to ideal
    df = get_distance_to_ideal_min(df, objective_cols)

    # Sort by Pareto rank first, then by distance to ideal
    df = df.sort_values(['pareto_rank', 'distance_to_ideal']).reset_index(drop=True)

    # Pareto front only (rank 1)
    pareto_front = df[df['pareto_rank'] == 1].head(5)

    # Best solutions (lowest distance to ideal)
    best_sols = df[df['distance_to_ideal'] == df['distance_to_ideal'].min()]
    best_sols_version = best_sols['version'].values

    pd.set_option('display.max_columns', None)
    print('\nFull DataFrame with ranks:')
    print(df)

    print('\nPareto front:')
    print(pareto_front)

    print('\nBest solution(s):')
    print(best_sols)

    print('\nVersion(s):')
    print(best_sols_version)

    # Parallel coordinates plot for the Pareto front
    conf_type, conf_num = args.config.split('_')
    
    fig = px.parallel_coordinates(
        # df,
        pareto_front,
        dimensions=objective_cols,
        color='distance_to_ideal',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            **{col: f'{col.capitalize()} (↓)' for col in objective_cols},
            'distance_to_ideal': 'Distance to Ideal'
        },
        title=f'Pareto Front Parallel Coordinates - {conf_type.capitalize()} {conf_num} {args.charging_strategy.capitalize()}',
    )

    parallel_plot_filepath = os.path.join(params.data_output_path,
                                          f'augmecon/parallel_plot_{args.config}_{args.charging_strategy}_{args.grid_points}gp.png')


    # df['highlight'] = df['version'].isin(best_sols_version).astype(int)
    #
    # fig = px.parallel_coordinates(
    #     df,
    #     dimensions=objective_cols,
    #     color='highlight',
    #     color_continuous_scale=[[0, 'lightgray'], [1, 'red']],
    #     labels={**{col: f'{col.capitalize()} (↓)' for col in objective_cols}, 'highlight': 'Best'},
    #     title=f'Pareto Front Parallel Coordinates - {conf_type.capitalize()} {conf_num} {args.charging_strategy.capitalize()}'
    # )

    fig.write_image(parallel_plot_filepath, scale=2)
    print(f'\nPlot saved to {parallel_plot_filepath}')

    # fig.show()


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
    main([
        '-c', 'config_1',
        '-s', 'opportunistic'
    ])