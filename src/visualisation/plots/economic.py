import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from src.config import params
from src.visualisation import io, style, style_helpers


def plot_num_cp(
        df: pd.DataFrame,
        version: str,
        save_img: bool = False,
) -> None:
    plt.figure(figsize=style.fig_size)

    ax = sns.barplot(
        x='config',
        y='num_cp',
        hue='strategy',
        data=df,
        palette='Set2',
    )

    style_helpers.setup(
        title='Number of Charging Points',
        ylabel='Number of Charging Points',
        xlabel='Configuration',
        legend=True,
        ax=ax,
    )

    configs = df['config'].unique()
    strategies = df['strategy'].unique()

    bars = [bar for container in ax.containers for bar in container]
    labels = []

    for config in configs:
        for strategy in strategies:
            row = df[(df['config'] == config) & (df['strategy'] == strategy)]
            if not row.empty:
                labels.append(row['p_cp_rated'].values[0])

    for bar, label in zip(bars, labels):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.125,
            f'{label} kW',
            ha='center',
            va='bottom',
            fontsize=style.tick_fontsize,
            fontweight='bold',
        )

    if save_img:
        io.save_figure(f'num_cp_plot_{params.num_of_evs}EVs_{version}.png')