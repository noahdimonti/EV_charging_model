import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from src.visualisation import plot_setups
from src.config import params


def plot_performance_heatmap(df: pd.DataFrame, title: str, y_label: str, filename: str, units: dict, higher_is_better: dict, cmap: str):
    """
    Plot a heatmap of performance metrics with annotated values and best-cell highlights.

    Args:
        df (pd.DataFrame): numeric dataframe with scenarios as index and metrics as columns
        title (str): plot title
        filename (str): file name to save the plot
        units (dict): dict mapping column names to units, e.g., {'Num CP':'CP', 'Rated power':'kW'}
        higher_is_better (dict): dict mapping column names to bool, True if higher is better
        cmap: colour palette
    """
    # normalize columns, invert if lower is better
    norm_df = df.copy()
    for col in df.columns:
        mn, mx = df[col].min(), df[col].max()
        if mx == mn:
            norm_df[col] = 0.5
        else:
            norm_df[col] = (df[col] - mn) / (mx - mn)
        if not higher_is_better[col]:
            norm_df[col] = 1 - norm_df[col]

    # annotate with units
    annot_df = df.copy().astype(str)
    for col in df.columns:
        unit = units.get(col, '')
        if unit:
            annot_df[col] = df[col].apply(lambda v: f'{v:.2f} {unit}')
        else:
            annot_df[col] = df[col].apply(lambda v: f'{v:.2f}')

    # plot
    plt.figure(figsize=(max(8, len(df.columns)*1.5), 5))
    ax = sns.heatmap(
        norm_df,
        cmap=cmap,
        annot=annot_df,
        fmt='',
        linewidths=0.8,
        linecolor='white',
        annot_kws={'size': 8.5, 'weight': 'bold'},
        cbar=True,
        cbar_kws={'label': 'Performance (higher = better)'}
    )

    # highlight best values per column
    for j, col in enumerate(df.columns):
        best_idx = norm_df[col].idxmax()
        i = list(df.index).index(best_idx)
        ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor='black', lw=2))

    # bold labels
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, weight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')
    ax.set_xlabel('Evaluation Metrics', fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
    plt.title(title, fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    plot_setups.save_plot(filename)


if __name__ == '__main__':
    data = {
        'Objective': [
            'Economic', 'Technical', 'Social',
            'Techno-economic', 'Socio-technical', 'Socio-economic',
            'Socio-techno-economic'
        ],
        'Num CP': [4.67, 9.33, 9.00, 5.33, 9.30, 6.16, 6.50],
        'Rated power': [2.03, 7.20, 7.20, 2.40, 7.20, 2.40, 2.40],
        'Peak increase': [3.08, 0.00, 3.13, 0.00, 0.00, 3.82, 0.00],
        'Peak-to-average': [2.5133, 2.4360, 2.4607, 2.4371, 2.3910, 2.4828, 2.3988],
        'Average SOC': [58.54, 78.08, 94.99, 73.81, 95.10, 93.04, 92.24],
        'Lowest SOC': [18.86, 24.32, 45.60, 24.01, 45.60, 45.60, 45.60]
    }
    df = pd.DataFrame(data).set_index('Objective')

    data2 = {
        'Scenario': [
            'Config 1 Opportunistic', 'Config 1 Flexible',
            'Config 2 Opportunistic', 'Config 2 Flexible',
            'Config 3 Opportunistic', 'Config 3 Flexible'
        ],
        'Num CP': [10, 10, 5, 4, 6, 4],
        'Rated power': [2.40, 2.40, 2.40, 2.40, 2.40, 2.40],
        'Peak increase': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00],
        'Peak-to-average': [2.3949, 2.3995, 2.3995, 2.3998, 2.3992, 2.3998],
        'Average SOC': [94.90, 91.21, 93.51, 90.40, 93.53, 89.87],
        'Lowest SOC': [72.87, 45.60, 64.83, 45.60, 65.96, 45.60]
    }

    df2 = pd.DataFrame(data2).set_index('Scenario')

    # define units
    units = {
        'Num CP': 'CP',
        'Rated power': 'kW',
        'Peak increase': '%',
        'Peak-to-average': '',
        'Average SOC': '%',
        'Lowest SOC': '%'
    }

    # define which direction is better
    higher_is_better = {
        'Num CP': False,
        'Rated power': False,
        'Peak increase': False,
        'Peak-to-average': False,
        'Average SOC': True,
        'Lowest SOC': True
    }

    # usage
    plot_performance_heatmap(
        df,
        title='Trade-Offs Between Objective Prioritisation',
        y_label='Objective',
        filename=f'objective_comparison_heatmap_{params.num_of_evs}EVs.png',
        units=units,
        higher_is_better=higher_is_better,
        cmap='YlGnBu'
    )

    plot_performance_heatmap(
        df2,
        title='Performance Evaluation of Charging Strategies',
        y_label='Scenario',
        filename=f'charging_strategies_heatmap_{params.num_of_evs}EVs.png',
        units=units,
        higher_is_better=higher_is_better,
        cmap='YlOrBr'
    )
