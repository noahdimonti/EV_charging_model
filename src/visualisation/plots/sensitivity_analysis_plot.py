import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import params


def plot_sensitivity(
        df: pd.DataFrame,
        metrics: list[str],
        y_labels: dict[str, str],
        x_col: str,
        title: str,
        filename: str,
        order: list[str],
) -> None:
    sns.set_theme(style='whitegrid', context='paper')

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes = axes.flatten()

    df = df.copy()
    df[x_col] = pd.Categorical(df[x_col], categories=order, ordered=True)
    df = df.sort_values(x_col)

    ylims = {
        'num_cp': (0, 10),
        'papr': (2.2, 2.6),
        'avg_soc_t_dep_percent': (50, 100),
        'lowest_soc': (50, 100),
    }

    offsets = {
        'num_cp': 0.5,
        'papr': 0.02,
        'avg_soc_t_dep_percent': 3,
        'lowest_soc': 3,
    }

    baseline = order[1]
    baseline_df = df[df[x_col] == baseline]

    for i, metric in enumerate(metrics):
        sns.lineplot(
            data=df,
            x=x_col,
            y=metric,
            marker='o',
            linewidth=2,
            color='#4C72B0',
            ax=axes[i],
        )

        axes[i].scatter(
            baseline_df[x_col],
            baseline_df[metric],
            color='#D62728',
            s=120,
            zorder=5,
        )

        axes[i].set_xlabel('')
        axes[i].set_ylabel('')
        axes[i].set_title(
            y_labels[metric],
            fontsize=15,
            fontweight='bold',
            pad=12,
        )
        axes[i].margins(x=0.1)
        axes[i].set_ylim(ylims[metric])

        axes[i].tick_params(
            axis='both',
            labelsize=14,
        )

        for label in axes[i].get_xticklabels():
            label.set_fontweight('bold')

        for label in axes[i].get_yticklabels():
            label.set_fontweight('bold')

        for x, y in zip(df[x_col], df[metric]):
            if metric == 'num_cp':
                label = f'{int(y)} CP'
            else:
                label = f'{y:.2f}'

            axes[i].text(
                x,
                y + offsets[metric],
                label,
                ha='center',
                fontsize=11,
                fontweight='bold',
            )

    fig.suptitle(
        title,
        fontsize=18,
        fontweight='bold',
    )

    plt.tight_layout(pad=2.5)

    filepath = os.path.join(params.plots_folder_path, filename)
    plt.savefig(filepath, dpi=300)
    plt.close()