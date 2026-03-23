import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from src.visualisation import style



def setup(title: str, ylabel: str, xlabel: str = None, legend=True, legend_col: int = 3, ax=None):
    """Helper function to set up plot aesthetics."""
    if ax is None:
        ax = plt.gca()

    if xlabel:
        ax.set_xlabel(xlabel, fontsize=style.label_fontsize, weight='bold')

    ax.set_ylabel(ylabel, fontsize=style.label_fontsize, weight='bold')
    ax.set_title(title, fontsize=style.title_fontsize, weight='bold')

    # Bold tick labels
    ax.tick_params(axis='both', labelsize=style.tick_fontsize)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight('bold')

    # Tilting tick labels
    # ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right')

    # Grid
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.6)

    # Spines (top and right)
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['top'].set_linewidth(1)
    ax.spines['right'].set_linewidth(1)

    # Legend
    if legend:
        ax.legend(
            loc='upper center',
            bbox_to_anchor=(0.5, -0.15),
            frameon=True,
            ncol=legend_col,
            prop={
                'weight': 'bold',
                'size': style.legend_fontsize
            },
        )

    plt.tight_layout()


def timeseries_setup(ax=None):
    if ax is None:
        ax = plt.gca()

    # Enhance the grid and axes
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=12))  # Minor ticks at 12 PM
    ax.grid(visible=True, which='minor', linestyle='--', linewidth=0.5, alpha=0.6)  # Grid for minor ticks
    ax.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.8)  # Grid for major ticks

    # Format x-axis to show day names
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Set major ticks for each day
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))  # Use abbreviated day names ('Mon', 'Tue', etc.)

    # Ensure minor ticks for clarity (optional)
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18, 24]))  # Minor ticks for every 6 hours
    ax.tick_params(axis='x', which='major', labelsize=12)  # Rotate day names for better readability

    # Bold tick labels
    ax.tick_params(axis='both', labelsize=style.tick_fontsize)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontweight('bold')
