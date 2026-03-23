import pandas as pd
import matplotlib.pyplot as plt
import os
import pickle
from src.config import params
from src.models.results.model_results import EvaluationMetrics, ModelResults


def build_model_results_filename(config: str, strategy: str, version: str) -> str:
    return f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'


def load_model_results(config: str, strategy: str, version: str) -> ModelResults:
    filename = build_model_results_filename(config, strategy, version)
    filepath = os.path.join(params.model_results_folder_path, filename)

    with open(filepath, 'rb') as f:
        return pickle.load(f)



def load_compiled_metrics(version: str, metrics_type: str = 'raw') -> pd.DataFrame:
    if metrics_type == 'raw':
        base_name = params.raw_val_metrics_filename_format
    elif metrics_type == 'formatted':
        base_name = params.formatted_metrics_filename_format
    else:
        raise ValueError(f'Unknown metrics_type: {metrics_type}')

    filename = f'{base_name}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.csv'
    filepath = os.path.join(params.compiled_metrics_folder_path, filename)

    return pd.read_csv(filepath, index_col=0)


def save_figure(filename: str):
    file_path = os.path.join(params.plots_folder_path, filename)
    plt.savefig(
        file_path,
        dpi=300,
        # transparent=True,
        bbox_inches='tight',
        pad_inches=0.2
    )