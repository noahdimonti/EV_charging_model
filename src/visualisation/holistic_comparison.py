import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params, ev_params, independent_variables
from src.visualisation import plot_setups
from src.visualisation import plot_configs
from pprint import pprint


# SPIDER CHART
# Data
labels = ['Fairness', 'Grid Impact', 'Cost']
values = [80, 65, 90]  # Example values (0-100 scale)

# Radar setup
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
values += values[:1]  # Repeat the first value to close the circle
angles += angles[:1]  # Repeat the first angle too

# Plot
fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.set_theta_offset(np.pi / 2)      # Start from top
ax.set_theta_direction(-1)          # Clockwise

# Draw the outline
ax.plot(angles, values, color='tab:blue', linewidth=2)
ax.fill(angles, values, color='tab:blue', alpha=0.25)

# Style axes
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, fontsize=12, weight='bold')

# Set r-labels inside the circle
ax.set_rlabel_position(180 / num_vars)
ax.set_yticks([20, 40, 60, 80])
ax.set_yticklabels(['20', '40', '60', '80'], fontsize=10)
ax.set_ylim(0, 100)

# Optional: circular grid style
ax.grid(True, linestyle='dotted', linewidth=1, alpha=0.7)

# Remove frame
ax.spines['polar'].set_visible(False)

plt.title('Performance Metrics Radar', fontsize=14, weight='bold', y=1.1)
plt.tight_layout()

plot_setups.save_plot('tests.png')
# plt.show()
