import numpy as np
import pandas as pd
from pandas.plotting import parallel_coordinates
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import ternary
from src.config import params
import os

pd.set_option('display.max_rows', None)


def plot_epsilon(config, charging_strategy, df: pd.DataFrame = None):
    if df is None:
        # filename = f'epsilon_constraint/epsilon_sweep_{config}_{charging_strategy}.csv'
        filename = f'augmecon_method/pareto.csv'
        filepath = os.path.join(params.data_output_path, filename)

        df = pd.read_csv(filepath)

    # df = df[['economic_objective', 'technical_objective', 'social_objective']]

    df = df[['economic', 'technical', 'social']]
    df.rename(columns={
        'economic': 'economic_objective',
        'technical': 'technical_objective',
        'social': 'social_objective',
    }, inplace=True)


    # Set up figure and axis
    fig, ax = plt.subplots(figsize=(8, 6))

    # Scatter plot with social objective as color
    sc = ax.scatter(
        df['economic_objective'],
        df['technical_objective'],
        c=df['social_objective'],
        cmap='viridis',  # or 'plasma', 'coolwarm', 'Blues', etc.
        edgecolor='k',
        alpha=0.8
    )

    # Colorbar to show social objective values
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Social Objective (Normalised)', fontsize=12)

    # Axis labels and limits
    ax.set_xlabel('Economic Objective (Normalised)', fontsize=12)
    ax.set_ylabel('Technical Objective (Normalised)', fontsize=12)
    # ax.set_xlim(0, 1)
    # ax.set_ylim(0, 1)
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.title('Social Objective as Heatmap over Economic–Technical Plane', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'social_obj_heatmap_{config}_{charging_strategy}.png')
    plt.show()



    # Create the heatmap
    fig = px.density_heatmap(
        df,
        x='economic_objective',
        y='technical_objective',
        z='social_objective',
        nbinsx=20,
        nbinsy=20,
        color_continuous_scale='Blues',
        labels={
            'economic_objective': 'Economic Objective',
            'technical_objective': 'Technical Objective',
            'social_objective': 'Social Objective'
        },
        title='Heatmap of Social Objective over Economic–Technical Plane'
    )

    fig.update_layout(
        # xaxis=dict(range=[0, 1]),
        # yaxis=dict(range=[0, 1]),
        coloraxis_colorbar=dict(title='Social Objective'),
    )

    fig.show()




    # Bubble map
    # Scale bubble size (optional tuning factor for visibility)
    bubble_scale = 0.5  # increase if bubbles are still small

    fig, ax = plt.subplots(figsize=(8, 6))

    # Bubble plot
    sc = ax.scatter(
        df['economic_objective'],
        df['technical_objective'],
        s=df['social_objective'] * bubble_scale,  # bubble size
        c=df['social_objective'],  # color (optional)
        cmap='viridis',
        edgecolor='k',
        alpha=0.7
    )

    # Add colorbar (optional — helps interpret bubble color)
    cbar = plt.colorbar(sc, ax=ax)
    cbar.set_label('Social Objective', fontsize=12)

    # Labels and limits
    ax.set_xlabel('Economic Objective', fontsize=12)
    ax.set_ylabel('Technical Objective', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)

    plt.title('Bubble Plot of Social Objective over Economic–Technical Plane', fontsize=14)
    plt.tight_layout()
    plt.savefig(f'bubble_plot_{config}_{charging_strategy}.png')
    plt.show()




    # 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(
        df['economic_objective'],  # x
        df['technical_objective'],  # y
        df['social_objective'],     # z
        c='blue', alpha=0.7
    )

    ax.set_xlabel('Economic Objective')
    ax.set_ylabel('Technical Objective')
    ax.set_zlabel('Social Objective')

    # ax.set_xlim(0, 1)
    # ax.set_ylim(0, 1)
    # ax.set_zlim(0, 1)
    # axis_range = (0, 1.1, 0.1)
    # ax.set_xticks(np.arange(axis_range[0], axis_range[1], axis_range[2]))
    # ax.set_yticks(np.arange(axis_range[0], axis_range[1], axis_range[2]))
    # ax.set_zticks(np.arange(axis_range[0], axis_range[1], axis_range[2]))

    plt.title('Pareto Front (3D)')

    plt.savefig(f'epsilon_sweep_3D_{config}_{charging_strategy}.png')
    plt.show()





    # Compute row-wise sum and normalised ratios for ternary plot
    df['sum'] = df['economic_objective'] + df['technical_objective'] + df['social_objective']
    df['econ_ratio'] = df['economic_objective'] / df['sum']
    df['tech_ratio'] = df['technical_objective'] / df['sum']
    df['social_ratio'] = df['social_objective'] / df['sum']

    # Create ternary plot
    fig = px.scatter_ternary(
        df,
        a='econ_ratio',
        b='tech_ratio',
        c='social_ratio',
        size='social_objective',  # Optional: visual cue for impact
        color='social_objective',  # Optional: heatmap shading
        size_max=15,
        color_continuous_scale='RdBu_r',  # Because lower social objective = better
    )

    # Update axis labels to appear directly on each side (not triangle tips)
    fig.update_layout(
        ternary=dict(
            aaxis=dict(title='Economic', min=0.0, linewidth=1),
            baxis=dict(title='Technical', min=0.0, linewidth=1),
            caxis=dict(title='Social', min=0.0, linewidth=1),
            sum=1
        ),
        title='Ternary Plot of Objective Composition (unnormalised inputs)'
    )

    fig.show()





