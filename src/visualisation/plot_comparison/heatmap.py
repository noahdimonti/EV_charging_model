import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import params
from src.visualisation import plot_setups

# replace these values with your actual numeric values (no units in df)
data = {
    'Objective': [
        'Economic', 'Technical', 'Social',
        'Techno-economic', 'Socio-technical', 'Socio-economic',
        'Socio-techno-economic'
    ],
    'N_CP': [4.67, 9.33, 9.00, 5.33, 9.30, 6.16, 6.5],
    'P_CP_rated_kW': [2.03, 7.20, 7.20, 2.40, 7.20, 2.40, 2.40],
    'P_peak_incr_pct': [3.08, 0.00, 3.13, 0.00, 0.00, 3.82, 0.00],
    'SOC_avg_dep_pct': [58.54, 78.08, 94.99, 73.81, 95.10, 93.04, 92.24],
    'SOC_low_dep_pct': [18.86, 24.32, 45.60, 24.01, 45.60, 45.60, 45.60]
}
df = pd.DataFrame(data).set_index('Objective')

# rename columns for nice x-axis labels
col_labels = {
    'N_CP': 'Num CP',
    'P_CP_rated_kW': 'Rated power',
    'P_peak_incr_pct': 'Peak increase',
    'SOC_avg_dep_pct': 'Average SOC',
    'SOC_low_dep_pct': 'Lowest SOC'
}
df = df.rename(columns=col_labels)

# which direction is better
higher_is_better = {
    'Num CP': False,
    'Rated power': False,
    'Peak increase': False,
    'Average SOC': True,
    'Lowest SOC': True
}

# normalize per column, inverting where lower is better
norm_df = df.copy()
for col in df.columns:
    mn, mx = df[col].min(), df[col].max()
    if mx == mn:
        norm_df[col] = 0.5
    else:
        norm_df[col] = (df[col] - mn) / (mx - mn)
    if not higher_is_better[col]:
        norm_df[col] = 1 - norm_df[col]

# format values with units
formats = {
    'Num CP': lambda v: f'{v:.2f} CP',
    'Rated power': lambda v: f'{v:.2f} kW',
    'Peak increase': lambda v: f'{v:.2f} %',
    'Average SOC': lambda v: f'{v:.2f} %',
    'Lowest SOC': lambda v: f'{v:.2f} %'
}
annot_df = df.copy().astype(str)
for col, fmt in formats.items():
    annot_df[col] = df[col].apply(fmt)

# plot heatmap
plt.figure(figsize=(8.5, 5))
ax = sns.heatmap(
    norm_df,
    cmap='YlGnBu',
    # cmap='crest',
    annot=annot_df,
    fmt='',
    linewidths=0.8,
    linecolor='white',
    annot_kws={'size': 7.5, 'weight': 'bold'},
    cbar=True,
    cbar_kws={'label': 'Performance (higher = better)'}
)

# highlight best values per column
for j, col in enumerate(df.columns):
    best_idx = norm_df[col].idxmax()
    i = list(df.index).index(best_idx)
    ax.add_patch(plt.Rectangle((j, i), 1, 1, fill=False, edgecolor='black', lw=2))

# tidy up labels
# ax.set_title('Comparison of Objective Combinations')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='right')

# Bold title
plt.title('Trade-offs Between Objective Prioritisation', fontsize=13, fontweight='bold', pad=15)

# Bold axis labels
ax.set_xlabel('Evaluation Metrics', fontsize=12, fontweight='bold')
ax.set_ylabel('Objective', fontsize=12, fontweight='bold')

plt.tight_layout()

plot_setups.save_plot(f'objective_comparison_heatmap_{params.num_of_evs}EVs.png')
