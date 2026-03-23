import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import params
from src.visualisation import io, style, style_helpers


def plot_soc_boxplot(
        df: pd.DataFrame,
        version: str,
        save_img: bool = False,
) -> None:
    plt.figure(figsize=style.fig_size)

    ax = sns.boxplot(
        x='config_num',
        y='soc_t_dep',
        hue='strategy',
        data=df,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'},
    )

    style_helpers.setup(
        title='Distribution of SOC at Departure Time',
        ylabel='SOC at Departure Time (%)',
        xlabel='Configuration',
        legend=True,
        ax=ax,
    )

    ax.tick_params(axis='x', labelsize=20)
    plt.ylim(0, 100)

    if save_img:
        io.save_figure(f'soc_boxplot_{params.num_of_evs}EVs_{version}.png')


def plot_num_charging_days(
        df: pd.DataFrame,
        version: str,
        save_img: bool = False,
) -> None:
    plt.figure(figsize=style.fig_size)

    ax = sns.barplot(
        x='config_num',
        y='num_charging_day',
        hue='strategy',
        data=df,
        palette='Set2',
    )

    style_helpers.setup(
        title='Number of Charging Days Comparison',
        ylabel='Average Number of Charging Days',
        xlabel='Configuration',
        legend=True,
        ax=ax,
    )

    ax.tick_params(axis='x', labelsize=20)

    if save_img:
        io.save_figure(f'num_charging_day_plot_{params.num_of_evs}EVs_{version}.png')


def plot_wait_time_boxplot(
        df: pd.DataFrame,
        version: str,
        save_img: bool = False,
        save_csv: bool = False,
) -> None:
    if save_csv:
        filepath = os.path.join(params.metrics_folder_path, 'wait_time_data.csv')
        df.to_csv(filepath, index=False)

    plt.figure(figsize=style.fig_size)

    ax = sns.boxplot(
        x='config_num',
        y='wait_time',
        hue='strategy',
        data=df,
        palette='Set2',
        medianprops={'linewidth': 2.5, 'color': 'black'},
    )

    style_helpers.setup(
        title='Distribution of Charging Wait Time on Arrival',
        ylabel='Wait Time (hours)',
        xlabel='Configuration',
        legend=True,
        ax=ax,
    )

    ax.tick_params(axis='x', labelsize=20)

    if save_img:
        io.save_figure(f'wait_time_boxplot_{params.num_of_evs}EVs_{version}.png')