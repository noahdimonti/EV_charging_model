import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import os
from src.config import params


def parallel_plot_pareto(df: pd.DataFrame, config: str, strategy: str):
    # Rename labels
    rename_dict = {
        'investor_score': 'Investor Score',
        'dso_score': 'DSO Score',
        'user_score': 'User Score'
    }
    df.rename(columns=rename_dict, inplace=True)

    plt.figure(figsize=(15, 5))

    metrics = ['Investor Score', 'DSO Score', 'User Score']

    # Get solutions and pareto rank columns
    parallel_df = df[metrics + ['pareto_rank']].copy()

    # Flip rank values manually for correct colouring
    parallel_df['pareto_rank_flipped'] = parallel_df['pareto_rank'].max() - parallel_df['pareto_rank'] + 1

    conf, num = config.split('_')

    fig_parallel = px.parallel_coordinates(
        parallel_df,
        color='pareto_rank_flipped',  # Use flipped rank for colour mapping
        dimensions=metrics,
        color_continuous_scale=px.colors.diverging.Tealrose[::-1],
        title=f'Parallel Coordinates Plot (Pareto Ranks) - {conf.capitalize()}uration {num} {strategy.capitalize()}'
    )

    # Correct colorbar labels back to original pareto_rank
    fig_parallel.update_layout(
        coloraxis_colorbar=dict(
            title='Pareto Rank',
            tickvals=parallel_df['pareto_rank_flipped'],
            ticktext=parallel_df['pareto_rank'],  # Show the real rank values
        )
    )

    # Save plot
    filename = f'pareto_parallel_{config}_{strategy}_{params.num_of_evs}EVs.png'
    filepath = os.path.join(params.plots_folder_path, 'sensitivity_analysis', filename)

    fig_parallel.write_image(filepath, scale=2)
    fig_parallel.show()

