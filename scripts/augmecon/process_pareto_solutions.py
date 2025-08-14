import pandas as pd
import numpy as np
import os
# import plotly.io as pio
# pio.renderers.default = 'browser'

import plotly.express as px
from src.config import params
from pprint import pprint


def main():
    # Parameters
    config = 'config_1'
    strategy = 'flexible'
    version = 'augmecon_test'
    grid_points = 20

    # Load your CSV
    filepath = os.path.join(params.data_output_path,
                            f'augmecon_method/pareto_{config}_{strategy}_social_primary_{grid_points}gp.csv')
    df = pd.read_csv(filepath)

    # Compute ranks
    objective_cols = ['social', 'economic', 'technical']
    df['pareto_rank'] = get_pareto_ranks_min(df[objective_cols])

    # Get distance to ideal
    df = get_distance_to_ideal_min(df, objective_cols)

    # Sort by Pareto rank first, then optionally by distance to ideal
    df = df.sort_values(['pareto_rank', 'distance_to_ideal']).reset_index(drop=True)

    # Pareto front only (rank 1)
    pareto_front = df[df['pareto_rank'] == 1]

    pd.set_option('display.max_columns', None)
    print('\nFull DataFrame with ranks:')
    print(df)
    print('\nPareto front:')
    print(pareto_front)

    # Parallel coordinates plot for the Pareto front
    conf_type, conf_num = config.split('_')
    fig = px.parallel_coordinates(
        df,
        dimensions=objective_cols,
        color='distance_to_ideal',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={**{col: col.capitalize() for col in objective_cols},
                'distance_to_ideal': 'Distance to Ideal'},
        title=f'Pareto Front Parallel Coordinates - {conf_type.capitalize()} {conf_num} {strategy.capitalize()}',
    )

    parallel_plot_filepath = os.path.join(params.data_output_path,
                                          f'augmecon_method/parallel_plot_{config}_{strategy}_{grid_points}gp.png')

    fig.write_image(parallel_plot_filepath, scale=2)
    # fig.show()


def get_pareto_ranks_min(df: pd.DataFrame) -> pd.Series:
    num_points = df.shape[0]
    ranks = np.zeros(num_points, dtype=int)
    remaining = set(range(num_points))
    current_rank = 1

    while remaining:
        current_front = set()
        for i in remaining:
            dominated = False
            for j in remaining:
                if i == j:
                    continue
                # For minimisation
                if (df.iloc[j] <= df.iloc[i]).all() and (df.iloc[j] < df.iloc[i]).any():
                    dominated = True
                    break
            if not dominated:
                current_front.add(i)

        for idx in current_front:
            ranks[idx] = current_rank

        remaining -= current_front
        current_rank += 1

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
    main()