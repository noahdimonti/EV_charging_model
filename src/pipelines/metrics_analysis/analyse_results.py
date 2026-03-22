import pandas as pd
import pickle
import os
from src.config import params
from src.models.results.model_results import compile_multiple_models_metrics, ModelResults, EvaluationMetrics
from pprint import pprint


def load_model(
        config: str,
        strategy: str,
        version: str) -> ModelResults:
    filename = f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
    filepath = os.path.join(params.model_results_folder_path, filename)

    with open(filepath, 'rb') as f:
        return pickle.load(f)


def analyse_multiple_models(configurations: list,
                            charging_strategies: list,
                            version: str,
                            save_df: bool = True) -> (pd.DataFrame, pd.DataFrame):
    formatted_models_metrics = {}
    raw_val_metrics = {}

    # Analyse multiple models from pkl files
    for config in configurations:
        for strategy in charging_strategies:
            try:
                results = load_model(config, strategy, version)

                # Get evaluation metrics from results
                evaluation_metrics = EvaluationMetrics(results)

                # Format and collect metrics
                formatted_metrics = evaluation_metrics.format_metrics()

                raw_val_metrics[f'{config}_{strategy}'] = evaluation_metrics.metrics
                formatted_models_metrics[f'{config}_{strategy}'] = formatted_metrics

            except FileNotFoundError:
                print(f'{config} {strategy} data is not available.')
                continue

    # Compile formatted models metrics
    formatted_filename = (f'{params.formatted_metrics_filename_format}_'
                          f'{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv')
    formatted_results = compile_multiple_models_metrics(formatted_models_metrics, filename=formatted_filename,
                                                        save_df=save_df)

    # Compile raw values models metrics
    raw_metrics_filename = (f'{params.raw_val_metrics_filename_format}_'
                            f'{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv')
    raw_metrics_results = compile_multiple_models_metrics(raw_val_metrics, filename=raw_metrics_filename,
                                                          save_df=save_df)

    return raw_metrics_results, formatted_results


def analyse_one_model(model_results: ModelResults):
    # Get evaluation metrics from results
    evaluation_metrics = EvaluationMetrics(model_results)

    # Format and collect metrics
    formatted_metrics = evaluation_metrics.format_metrics()

    df_metrics = pd.DataFrame(formatted_metrics)

    print(df_metrics)

