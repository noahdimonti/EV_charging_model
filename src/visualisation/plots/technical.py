import matplotlib.pyplot as plt
import pandas as pd
from src.config import params
from src.visualisation import io, style, style_helpers
from src.visualisation.labels import format_config_label


def plot_num_ev_charging(
        df: pd.DataFrame,
        config: str,
        charging_strategies: list[str],
        version: str,
        save_img: bool = False,
) -> None:

    plt.figure(figsize=style.fig_size)
    ax = plt.gca()

    for strategy in charging_strategies:
        sub = df[(df['config'] == config) & (df['strategy'] == strategy)]

        if sub.empty:
            continue

        # since df already filtered to charging_power > 0
        occupancy = sub.groupby('time').size()

        ax.step(
            occupancy.index,
            occupancy.values,
            where='post',
            label=sub['strategy_label'].iloc[0],
            linewidth=2.5
        )

    config_label = format_config_label(config)

    style_helpers.setup(
        title=f'Number of EVs Charging - {config_label}',
        ylabel='Number of EVs charging',
        xlabel='Day/Time',
        legend=True,
        legend_col=2,
        ax=ax,
    )

    style_helpers.timeseries_setup(ax=ax)
    ax.set_ylim(0, 11)

    plt.tight_layout()

    if save_img:
        io.save_figure(f'num_evs_charging_{params.num_of_evs}EVs_{config}_{version}.png')