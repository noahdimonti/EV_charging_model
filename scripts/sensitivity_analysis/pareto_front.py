import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from scripts.sensitivity_analysis.sensitivity_analysis_tools import holistic_metrics, step
from src.config import params


def is_dominated(row, others):
    # A row is dominated if there's *any* other row that is >= in all objectives and > in at least one
    return any(
        (other >= row).all() and (other > row).any()
        for _, other in others.iterrows()
    )


def pareto_front(df):
    front_indices = []
    for i, row in df.iterrows():
        others = df.drop(index=i)
        if not is_dominated(row, others):
            front_indices.append(i)
    return front_indices


data = holistic_metrics[['investor_score', 'dso_score', 'user_score']]

pareto_idxs = pareto_front(data)
# print("Pareto front indices:", pareto_idxs)
# print("Pareto-optimal rows:\n", holistic_metrics.loc[pareto_idxs])


def pareto_rank(df: pd.DataFrame) -> pd.Series:
    """
    Assign Pareto ranks to each row in the DataFrame.

    Parameters:
    - df: A DataFrame where each row is a solution and each column is a normalized objective (higher is better).

    Returns:
    - A Series with Pareto rank for each row (1 = best Pareto front).
    """
    num_points = df.shape[0]
    ranks = np.zeros(num_points, dtype=int)
    current_rank = 1
    remaining = set(range(num_points))

    while remaining:
        current_front = set()
        for i in remaining:
            is_dominated = False
            for j in remaining:
                if i != j:
                    # Check if row j dominates row i
                    if all(df.iloc[j] >= df.iloc[i]) and any(df.iloc[j] > df.iloc[i]):
                        is_dominated = True
                        break
            if not is_dominated:
                current_front.add(i)
        for i in current_front:
            ranks[i] = current_rank
        remaining -= current_front
        current_rank += 1

    return pd.Series(ranks, index=df.index, name="pareto_rank")


ranks = pareto_rank(data)
final_df = holistic_metrics.assign(pareto_rank=ranks).sort_values("pareto_rank")
print(final_df)

pareto_front_filename = f'{params.project_root}/data/outputs/metrics/pareto_front_{step}step.csv'

final_df.to_csv(pareto_front_filename)


# Load the previously saved DataFrame
df = pd.read_csv(pareto_front_filename, index_col=0)

# Rename labels
rename_dict = {
    'investor_score': 'Investor Score',
    'dso_score': 'DSO Score',
    'user_score': 'User Score'
}
df.rename(columns=rename_dict, inplace=True)

# 1. 2D Scatter Plots: Pairwise trade-offs
plt.figure(figsize=(15, 5))

metrics = ['Investor Score', 'DSO Score', 'User Score']
pairs = [('Investor Score', 'DSO Score'),
         ('Investor Score', 'User Score'),
         ('DSO Score', 'User Score')]

for i, (x, y) in enumerate(pairs, 1):
    plt.subplot(1, 3, i)
    sns.scatterplot(data=df, x=x, y=y, hue='pareto_rank', palette='viridis', s=70)
    plt.title(f'{x} vs {y}')
    plt.xlabel(x)
    plt.ylabel(y)
    plt.legend(title='Pareto Rank')

plt.tight_layout()

plt.savefig(f'{params.project_root}/data/outputs/plots/pareto_front.png', dpi=300)
# plt.show()

# 2. Parallel Coordinates Plot
parallel_df = df[metrics + ['pareto_rank']].copy()
parallel_df['pareto_rank'] = parallel_df['pareto_rank'].astype(int)  # Convert for color mapping

# Flip rank values manually for correct colouring
parallel_df['pareto_rank_flipped'] = parallel_df['pareto_rank'].max() - parallel_df['pareto_rank'] + 1

fig_parallel = px.parallel_coordinates(
    parallel_df,
    color='pareto_rank_flipped',  # Use flipped rank for colour mapping
    dimensions=metrics,
    color_continuous_scale=px.colors.diverging.Tealrose[::-1],
    title="Parallel Coordinates Plot (Pareto Ranks) - Config 1 Opportunistic"
)

# Correct colorbar labels back to original pareto_rank
fig_parallel.update_layout(
    coloraxis_colorbar=dict(
        title="Pareto Rank",
        tickvals=parallel_df['pareto_rank_flipped'],
        ticktext=parallel_df['pareto_rank'],  # Show the real rank values
    )
)


fig_parallel.write_image(f'{params.project_root}/data/outputs/plots/pareto_parallel.png', scale=2)
# fig_parallel.show()

