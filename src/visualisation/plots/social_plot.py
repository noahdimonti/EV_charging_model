import os

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
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


def plot_wait_time_soc_scatter(
        df: pd.DataFrame,
        version: str,
        save_img: bool = False,
        save_csv: bool = False,
        hue: str | None = 'strategy',
        show_trend: bool = True,
        ax: Axes | None = None,
) -> Axes:
    required_columns = {'wait_time', 'soc_before_charging'}
    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        raise ValueError(
            f'Dataframe is missing required columns: {sorted(missing_columns)}'
        )

    plot_df = df.dropna(subset=['wait_time', 'soc_before_charging']).copy()

    if plot_df.empty:
        raise ValueError('No wait time / SOC points are available to plot.')

    if save_csv:
        filepath = os.path.join(
            params.metrics_folder_path,
            f'wait_time_soc_scatter_{params.num_of_evs}EVs_{version}.csv',
        )
        plot_df.to_csv(filepath, index=False)

    if ax is None:
        plt.figure(figsize=style.fig_size)
        ax = plt.gca()

    scatter_kwargs = {
        'data': plot_df,
        'x': 'wait_time',
        'y': 'soc_before_charging',
        's': 110,
        'alpha': 0.75,
        'edgecolor': 'white',
        'linewidth': 0.6,
        'ax': ax,
    }

    show_legend = False
    if hue is not None and hue in plot_df.columns:
        scatter_kwargs['hue'] = hue
        scatter_kwargs['palette'] = 'Set2'
        show_legend = True
    else:
        scatter_kwargs['color'] = '#2a6f97'

    sns.scatterplot(**scatter_kwargs)

    if show_trend and len(plot_df) > 1:
        sns.regplot(
            data=plot_df,
            x='wait_time',
            y='soc_before_charging',
            scatter=False,
            ci=None,
            line_kws={
                'color': 'black',
                'linewidth': 2.5,
                'alpha': 0.85,
            },
            ax=ax,
        )

    style_helpers.setup(
        title='Waiting Time vs SOC Before Charging',
        ylabel='SOC Before Charging (%)',
        xlabel='Waiting Time (hours)',
        legend=show_legend,
        legend_col=3,
        ax=ax,
    )

    ax.set_xlim(left=0)
    ax.set_ylim(0, 100)

    if save_img:
        io.save_figure(f'wait_time_soc_scatter_{params.num_of_evs}EVs_{version}.png')

    return ax
