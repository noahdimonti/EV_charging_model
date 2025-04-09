import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import pickle
from src.config import params
from src.utils.model_results import ModelResults

fig_size = (12, 8)


def get_model_results_data(config: str, strategy: str, version: str):
    folder_path = os.path.join(params.model_results_folder_path)
    filename = f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
    file_path = os.path.join(folder_path, filename)

    with open(file_path, 'rb') as f:
        results = pickle.load(f)

    return results


def get_metrics(version: str):
    file_path = os.path.join(params.compiled_metrics_folder_path, params.raw_val_metrics_filename_format)
    filename = f'{file_path}_{version}.csv'
    metrics = pd.read_csv(filename, index_col='Unnamed: 0')

    return metrics


def setup(title, ylabel, legend=True):
    """Helper function to set up plot aesthetics."""
    plt.ylabel(ylabel)
    plt.title(title)

    # Add grid
    plt.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.3)

    # Add top and right borders (spines)
    ax = plt.gca()
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['top'].set_linewidth(1)
    ax.spines['right'].set_linewidth(1)

    # Add a legend if specified
    if legend:
        ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=3)

    # Adjust layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)


def save_plot(filename: str):
    file_path = os.path.join(params.plots_folder_path, filename)
    plt.savefig(file_path, dpi=300)