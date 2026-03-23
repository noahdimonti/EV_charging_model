import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import params
from src.visualisation import io, style, style_helpers


def plot_objective_soc_boxplot(
    df: pd.DataFrame,
    save_img: bool = False,
) -> None:
    plt.figure(figsize=style.fig_size)

    ax = sns.boxplot(
        x='version_label',
        y='soc_t_dep',
        hue='version_label',
        data=df,
        palette='tab10',
        legend=False,
        medianprops={'linewidth': 2.5, 'color': 'black'},
    )

    style_helpers.setup(
        title='Aggregated SOC Distribution at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Objective',
        legend=False,
        ax=ax,
    )

    ax.set_ylim(0, 100)
    plt.tight_layout()

    if save_img:
        io.save_figure(f'objective_comparison_soc_{params.num_of_evs}EVs.png')


def plot_objective_wait_time_boxplot(
    df: pd.DataFrame,
    save_img: bool = False,
) -> None:
    plt.figure(figsize=style.fig_size)

    ax = sns.boxplot(
        x='version_label',
        y='wait_time',
        hue='version_label',
        data=df,
        palette='Set2',
        legend=False,
        medianprops={'linewidth': 2.5, 'color': 'black'},
    )

    style_helpers.setup(
        title='Aggregated Charging Wait Time Distribution on Arrival',
        ylabel='Wait Time (hours)',
        xlabel='Objective',
        legend=False,
        ax=ax,
    )

    plt.tight_layout()

    if save_img:
        io.save_figure(
            f'objective_comparison_wait_time_boxplot_{params.num_of_evs}EVs.png'
        )