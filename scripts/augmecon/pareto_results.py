import pandas as pd
from scripts.augmecon.process_pareto_solutions import get_pareto_solutions


def main():
    df = get_pareto_solutions(
        'config_2',
        'flexible',
        10
    )

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


if __name__ == '__main__':
    main()