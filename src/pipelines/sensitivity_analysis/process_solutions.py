import pandas as pd
import numpy as np
import os
from src.pipelines.sensitivity_analysis.pareto_front import get_pareto_ranks
from src.config import params


def normalise_solution_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop('Unnamed: 0', axis=1)
    normalised = pd.DataFrame(index=df.index)
    for col in df.columns:
        min_val = df[col].min()
        max_val = df[col].max()
        normalised[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 0

    print(f'normalised: {normalised}')

    return normalised


def get_holistic_scores(df: pd.DataFrame) -> pd.DataFrame:
    normalised = normalise_solution_metrics(df.copy())

    # Create holistic score dataframe
    holistic_scores = pd.DataFrame(columns=['investor_score', 'dso_score', 'user_score'])
    holistic_scores = pd.concat(
        [holistic_scores, normalised[['economic_weight', 'technical_weight', 'social_weight']]], axis=1)
    holistic_scores = pd.concat(
        [df['total_objective_value'], holistic_scores], axis=1
    )

    # Economic score
    holistic_scores['investor_score'] = 1 - normalised['investment_cost']

    # Technical score
    holistic_scores['dso_score'] = ((1 - normalised['avg_p_peak']) *
                                    (1 - normalised['avg_papr']) *
                                    (1 - normalised['avg_daily_peak_increase']))

    # Social score - NOT FINALISED
    holistic_scores['user_score'] = ((normalised['avg_soc_t_dep_percent']) *  # average SOC
                                     (1 - normalised['soc_range']))  # fairness

    return holistic_scores


def assign_pareto_ranks(holistic_scores: pd.DataFrame) -> pd.DataFrame:
    # Get solution columns and pareto ranks
    solutions = holistic_scores[['investor_score', 'dso_score', 'user_score']]
    ranks = get_pareto_ranks(solutions)

    # Append pareto ranks to holistic metrics dataframe
    holistic_with_pareto_ranks = holistic_scores.assign(pareto_rank=ranks).sort_values('pareto_rank')

    return holistic_with_pareto_ranks


def get_distance_to_ideal(df: pd.DataFrame) -> pd.DataFrame:
    # Compute Euclidean distance to the ideal point (1, 1, 1)
    df['distance_to_ideal'] = np.sqrt(
        ((1 - df['investor_score']) ** 2) +
        ((1 - df['dso_score']) ** 2) +
        ((1 - df['user_score']) ** 2)
    )

    return df


def get_pareto_results(
        config: str,
        strategy: str,
        num_ev: int,
        step: float,
        version: str,
        sens_analysis_res: pd.DataFrame = None) -> (pd.DataFrame, pd.DataFrame):
    # Get raw data from sensitivity analysis file
    if sens_analysis_res is None:
        sens_filename = (f'sensitivity_analysis_'
                         f'{config}_{strategy}_{num_ev}EVs_{params.num_of_days}days_{step}step.csv')
        file_path = os.path.join(params.sensitivity_analysis_res_path, sens_filename)
        df = pd.read_csv(file_path)
    else:
        df = sens_analysis_res

    print(f'df: {df}')

    # Convert raw data into holistic scores and assign pareto ranks
    scores = get_holistic_scores(df)
    pareto = assign_pareto_ranks(scores)

    # Calculate the scores distance to ideal
    holistic_df = get_distance_to_ideal(pareto)

    # Sort solutions
    holistic_df = holistic_df.sort_values(['pareto_rank', 'distance_to_ideal', 'total_objective_value'])

    # Save holistic pareto front dataframe
    pareto_front_filename = (f'holistic_pareto_front_'
                             f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{step}step_{version}.csv')
    pareto_front_filepath = os.path.join(params.metrics_folder_path, 'holistic_metrics', pareto_front_filename)

    holistic_df.to_csv(pareto_front_filepath)
    print(f'\nHolistic scores with pareto ranks dataframe saved to:\n{pareto_front_filepath}')

    # Get solutions with the highest pareto rank
    pareto_front = holistic_df.loc[holistic_df['pareto_rank'] == 1]
    print(f'\nPareto front: \n{pareto_front}')

    # Get the best solution
    best_solution = pareto_front.head(1)
    print(f'\nBest solution: \n{best_solution}')

    return holistic_df, best_solution
