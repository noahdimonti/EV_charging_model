import pandas as pd
import numpy as np
import itertools
import os
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.config import params
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from pprint import pprint


def run_sensitivity_analysis(step: float, config: str, strategy: str, version: str,
                             verbose: bool, time_limit: int, mip_gap: float) -> pd.DataFrame:
    # Generate weights that sum to 1
    step = step
    w_vals = np.arange(0, 1 + step, step)

    weight_dicts = []
    for w1, w2 in itertools.product(w_vals, repeat=2):
        w3 = 1 - w1 - w2
        if 0 <= w3 <= 1:
            weight_dicts.append({
                'economic_weight': w1,
                'technical_weight': w2,
                'social_weight': round(w3, 10)
            })

    # Initialise a dataframe to store results
    df = pd.DataFrame()

    # Run optimisation for each weight
    for i, weights in enumerate(weight_dicts):
        print(f'-------------------------------------------------------------')
        print(f'-------------------------------------------------------------')
        print(f'\nIteration no: {i}')
        print(f'Objective weights:')
        pprint(weights, sort_dicts=False)

        # Run model and analyse results
        results = run_optimisation_model(
            config=config,
            charging_strategy=strategy,
            version=version,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap,
            save_model=False
        )
        raw, formatted = analyse_results(
            configurations=[config],
            charging_strategies=[strategy],
            version=version,
            save_df=False,
            model_results=results
        )

        # Store results in a dataframe
        df = pd.concat([raw, df], axis=1)

    # Transpose df so each row is one config
    df = df.T

    # Save compiled df to csv
    filename = (f'sensitivity_analysis_'
                f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{step}step.csv')
    file_path = os.path.join(params.sensitivity_analysis_res_path, filename)
    df.to_csv(file_path)

    print(f'Compiled sensitivity analysis results saved to:\n{file_path}\n')

    return df
