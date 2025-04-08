import matplotlib.pyplot as plt

fig_size = (12, 8)

def setup_plot(title, suptitle, ylabel, legend=True):
    """Helper function to set up plot aesthetics."""
    plt.ylabel(ylabel)
    plt.title(title)
    plt.suptitle(suptitle, fontsize=12, fontweight='bold')

    # Add grid
    plt.grid(visible=True, which='major', linestyle='--', linewidth=1, alpha=0.3)

    # Add top and right borders (spines)
    ax = plt.gca()
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['top'].set_color('black')
    ax.spines['right'].set_color('black')
    ax.spines['top'].set_linewidth(1)
    ax.spines['right'].set_linewidth(1)

    # Add a legend if specified
    if legend:
        ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, -0.15), frameon=False, ncol=2)

    # Adjust layout
    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.2)
