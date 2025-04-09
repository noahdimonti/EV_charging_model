import pandas as pd
import pickle
import os
from src.config import params
from src.utils.model_results import compile_multiple_models_metrics
from src.visualisation.plot_results import plot_p_ev, plot_agg_p_ev, plot_agg_total_demand, plot_ev_charging_schedule
from pprint import pprint


def analyse_results(configurations, charging_strategies, version, num_ev):
    pd.set_option('display.max_columns', None)

    formatted_models_metrics = {}
    raw_val_metrics = {}

    for config in configurations:
        for strategy in charging_strategies:
            folder_path = f'data/outputs/models/{config}_{strategy}_{num_ev}EVs_7days_{version}.pkl'
            filename = os.path.join(params.project_root, folder_path)

            with open(filename, 'rb') as f:
                results = pickle.load(f)

            # Format metrics
            formatted_metrics = results.format_metrics()

            # Collect metrics
            raw_val_metrics[f'{config}_{strategy}'] = results.metrics
            formatted_models_metrics[f'{config}_{strategy}'] = formatted_metrics

    # Compile formatted models metrics
    formatted_filename = f'{params.formatted_metrics_filename_format}_{version}.csv'
    formatted_results = compile_multiple_models_metrics(formatted_models_metrics, filename=formatted_filename)

    # Compile raw values models metrics
    raw_metrics_filename = f'{params.raw_val_metrics_filename_format}_{version}.csv'
    raw_metrics_results = compile_multiple_models_metrics(raw_val_metrics, filename=raw_metrics_filename)

    return raw_metrics_results, formatted_results
