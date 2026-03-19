import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import io, PIL.Image
from IPython.core.pylabtools import figsize

from src.config import params


def pareto_parallel_plot(config, charging_strategy, grid_points, pareto_df, num_sol_displayed):
    # Parallel coordinates plot for the Pareto front
    conf_type, conf_num = config.split('_')

    objective_cols = ['social', 'economic', 'technical']

    fig = px.parallel_coordinates(
        pareto_df,
        dimensions=objective_cols,
        color='distance_to_ideal',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            **{col: f'{col.capitalize()}' for col in objective_cols},
            'distance_to_ideal': 'Distance to Ideal'
        },
        title=f'{conf_type.capitalize()}uration {conf_num} {charging_strategy.capitalize()}',
    )

    # Make layout tight
    fig.update_layout(
        margin=dict(l=50, r=50, t=100, b=50)  # adjust left, right, top, bottom margins
    )

    parallel_plot_filepath = os.path.join(params.data_output_path,
                                          f'plots/parallel_plot_{config}_{charging_strategy}_{grid_points}gp_{num_sol_displayed}sols.png')


    fig.write_image(parallel_plot_filepath, scale=1)
    print(f'\nPlot saved to {parallel_plot_filepath}')


def combine_parallel_plots(image_paths, nrows=3, ncols=2):
    """
    Combine multiple saved parallel plots into a single figure grid.

    Args:
        image_paths (list): list of filepaths to your saved images
        output_path (str): path to save the combined figure
        ncols (int): number of columns in grid (default 5 for one row of 5)
    """
    n_images = len(image_paths)
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 4, nrows * 3),
                             constrained_layout=False)

    axes = axes.flatten()

    for i, img_path in enumerate(image_paths):
        img_path = os.path.join(params.plots_folder_path, img_path)
        img = mpimg.imread(img_path)
        axes[i].imshow(img, aspect='auto')
        axes[i].axis('off')

    # Hide any unused axes
    for j in range(n_images, len(axes)):
        axes[j].axis('off')

    # Remove all space between subplots
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0,
                        wspace=0, hspace=0)

    out_path = os.path.join(params.plots_folder_path, 'all_pareto_parallel.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()



image_paths = [
    'parallel_plot_config_1_opportunistic_20gp_4sols.png',
    'parallel_plot_config_1_flexible_20gp_4sols.png',
    'parallel_plot_config_2_opportunistic_20gp_4sols.png',
    'parallel_plot_config_2_flexible_10gp_4sols.png',
    'parallel_plot_config_3_opportunistic_20gp_4sols.png',
]
combine_parallel_plots(image_paths)


