import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import pickle
from src.config import params
from src.visualisation import plot_configs
from src.models.results.model_results import ModelResults, EvaluationMetrics

fig_size = (12, 8)


def get_model_results_data(config: str, strategy: str, version: str) -> EvaluationMetrics:
    filename = f'{config}_{strategy}_{params.num_of_evs}EVs_{params.num_of_days}days_{version}.pkl'
    file_path = os.path.join(params.model_results_folder_path, filename)

    with open(file_path, 'rb') as f:
        results = pickle.load(f)

    # Get evaluation metrics
    eval_metrics = EvaluationMetrics(results)

    return eval_metrics


def get_metrics(version: str):
    file_path = os.path.join(params.compiled_metrics_folder_path, params.raw_val_metrics_filename_format)
    filename = f'{file_path}_{version}.csv'
    metrics = pd.read_csv(filename, index_col='Unnamed: 0')

    return metrics


# def setup(title, ylabel, legend=True):
#     """Helper function to set up plot aesthetics."""
#     plt.ylabel(ylabel)
#     plt.title(title)
#
#     # Add grid
#     plt.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.3)
#
#     # Add top and right borders (spines)
#     ax = plt.gca()
#     ax.spines['top'].set_visible(True)
#     ax.spines['right'].set_visible(True)
#     ax.spines['top'].set_color('black')
#     ax.spines['right'].set_color('black')
#     ax.spines['top'].set_linewidth(1)
#     ax.spines['right'].set_linewidth(1)
#
#     # Add a legend if specified
#     if legend:
#         ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=4)
#
#     # Adjust layout
#     plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)
#
#     plt.tight_layout()


def setup(title: str, ylabel: str, xlabel: str = None, legend=True, legend_col: int = 3, ax=None):
    """Helper function to set up plot aesthetics."""
    if ax is None:
        ax = plt.gca()

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=plot_configs.label_fontsize, weight='bold')

    ax.set_ylabel(ylabel, fontsize=plot_configs.label_fontsize, weight='bold')
    ax.set_title(title, fontsize=plot_configs.title_fontsize, weight='bold')

    # Bold tick labels
    ax.tick_params(axis='both', labelsize=plot_configs.tick_fontsize)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight('bold')

    # Tilting tick labels
    # ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')

    # Grid
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.6)

    # Spines (top and right)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['top'].set_linewidth(1)
    ax.spines['right'].set_linewidth(1)

    # Legend
    if legend:
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            frameon=True,
            ncol=legend_col,
            prop={
                'weight': 'bold',
                'size': plot_configs.legend_fontsize
            },
        )

    plt.tight_layout()


def timeseries_setup(ax=None):
    if ax is None:
        ax = plt.gca()

    # Enhance the grid and axes
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=12))  # Minor ticks at 12 PM
    ax.grid(visible=True, which='minor', linestyle='--', linewidth=0.5, alpha=0.6)  # Grid for minor ticks
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.8)  # Grid for major ticks

    # Format x-axis to show day names
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Set major ticks for each day
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))  # Use abbreviated day names ('Mon', 'Tue', etc.)

    # Ensure minor ticks for clarity (optional)
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18, 24]))  # Minor ticks for every 6 hours
    ax.tick_params(axis='x', which='major', labelsize=12)  # Rotate day names for better readability


def save_plot(filename: str):
    file_path = os.path.join(params.plots_folder_path, filename)
    plt.savefig(
        file_path,
        dpi=300,
        transparent=True,
        bbox_inches='tight',
        pad_inches=0
    )