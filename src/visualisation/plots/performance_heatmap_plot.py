import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.visualisation import io


def normalise_heatmap_df(
        df: pd.DataFrame,
        higher_is_better: dict[str, bool],
) -> pd.DataFrame:
    norm_df = df.copy()

    for col in df.columns:
        col_min = df[col].min()
        col_max = df[col].max()

        if col_max == col_min:
            norm_df[col] = 0.5
        else:
            norm_df[col] = (df[col] - col_min) / (col_max - col_min)

        if not higher_is_better[col]:
            norm_df[col] = 1 - norm_df[col]

    return norm_df


def build_heatmap_annotation_df(
        df: pd.DataFrame,
        units: dict[str, str],
        formatters: dict[str, str] | None = None,
) -> pd.DataFrame:
    if formatters is None:
        formatters = {}

    annot_df = df.copy()

    for col in df.columns:
        fmt = formatters.get(col, '{:.2f}')
        unit = units.get(col, '')

        if unit:
            annot_df[col] = df[col].apply(lambda value: f'{fmt.format(value)} {unit}')
        else:
            annot_df[col] = df[col].apply(lambda value: fmt.format(value))

    return annot_df


def plot_performance_heatmap(
        df: pd.DataFrame,
        title: str,
        y_label: str,
        higher_is_better: dict[str, bool],
        units: dict[str, str],
        filename: str | None = None,
        formatters: dict[str, str] | None = None,
        cmap: str = 'YlGnBu',
        save_img: bool = False,
) -> None:
    norm_df = normalise_heatmap_df(df, higher_is_better)
    annot_df = build_heatmap_annotation_df(df, units, formatters)

    plt.figure(figsize=(max(8, len(df.columns) * 1.5), max(4, len(df.index) * 0.7)))

    ax = sns.heatmap(
        norm_df,
        cmap=cmap,
        annot=annot_df,
        fmt='',
        linewidths=0.8,
        linecolor='white',
        cbar=True,
        cbar_kws={'label': 'Normalised performance (higher = better)'},
        annot_kws={'size': 8.5, 'weight': 'bold'},
    )

    ax.set_xlabel('Evaluation Metrics', fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, weight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')

    plt.title(title, fontsize=13, fontweight='bold', pad=15)
    plt.tight_layout()

    if save_img and filename:
        io.save_figure(filename)