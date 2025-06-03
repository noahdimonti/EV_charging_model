import pandas as pd
import pickle
import os
from src.config import params
from src.models.results.model_results import compile_multiple_models_metrics, ModelResults
from pprint import pprint


def analyse_results(configurations: list,
                    charging_strategies: list,
                    version: str,
                    save_df: bool = True,
                    model_results: ModelResults = None) -> (pd.DataFrame, pd.DataFrame):
    formatted_models_metrics = {}
    raw_val_metrics = {}

    # Analyse if model_results object is not passed in
    if model_results is None:
        for config in configurations:
            for strategy in charging_strategies:
                folder_path = f'data/outputs/models/{config}_{strategy}_{params.num_of_evs}EVs_7days_{version}.pkl'
                filename = os.path.join(params.project_root, folder_path)

                with open(filename, 'rb') as f:
                    results = pickle.load(f)

                # Format and collect metrics
                formatted_metrics = results.format_metrics()

                raw_val_metrics[f'{config}_{strategy}'] = results.metrics
                formatted_models_metrics[f'{config}_{strategy}'] = formatted_metrics

    # If model_results object is provided
    else:
        # Get config and strategy
        config = model_results.config.value
        strategy = model_results.charging_strategy.value

        # Format and collect metrics
        formatted_metrics = model_results.format_metrics()

        raw_val_metrics[f'{config}_{strategy}'] = model_results.metrics
        formatted_models_metrics[f'{config}_{strategy}'] = formatted_metrics

    # Compile formatted models metrics
    formatted_filename = f'{params.formatted_metrics_filename_format}_{params.num_of_evs}EVs_{version}.csv'
    formatted_results = compile_multiple_models_metrics(formatted_models_metrics, filename=formatted_filename, save_df=save_df)

    # Compile raw values models metrics
    raw_metrics_filename = f'{params.raw_val_metrics_filename_format}_{params.num_of_evs}EVs_{version}.csv'
    raw_metrics_results = compile_multiple_models_metrics(raw_val_metrics, filename=raw_metrics_filename, save_df=save_df)

    return raw_metrics_results, formatted_results
