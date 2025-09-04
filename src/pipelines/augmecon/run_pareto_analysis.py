import pandas as pd

from src.pipelines.augmecon.process_pareto_solutions import get_pareto_solutions
from src.visualisation.pareto_parallel import pareto_parallel_plot


def main():
    config = 'config_2'
    strategy = 'flexible'
    grid_points = 10

    df = get_pareto_solutions(
        config,
        strategy,
        grid_points
    )

    # Pareto front only (rank 1)
    pareto_df = df[df['pareto_rank'] == 1].head(5)
    pareto_df = pareto_df.round(2)

    # Best solutions (lowest distance to ideal)
    best_sols = df[df['distance_to_ideal'] == df['distance_to_ideal'].min()]
    best_sols_version = best_sols['version'].values

    pd.set_option('display.max_columns', None)
    print('\nFull DataFrame with ranks:')
    print(df)

    print('\nPareto front:')
    print(pareto_df)

    print('\nBest solution(s):')
    print(best_sols)

    print('\nVersion(s):')
    print(best_sols_version)

    normalised_df = pareto_df.copy()
    for col in ['social', 'economic', 'technical']:
        normalised_df[col] = 1 - (pareto_df[col] - pareto_df[col].min()) / (pareto_df[col].max() - pareto_df[col].min())

    pareto_parallel_plot(
        config,
        strategy,
        grid_points,
        # normalised_df
        pareto_df
    )


if __name__ == '__main__':
    main()