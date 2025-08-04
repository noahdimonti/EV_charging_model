import pandas as pd
from pandas.plotting import parallel_coordinates
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import params
import os

def plot(config, charging_strategy):
    filename = f'scripts/epsilon_constraint/epsilon_sweep_{config}_{charging_strategy}.csv'
    filepath = os.path.join(params.project_root, filename)

    df = pd.read_csv(filepath)
    df = df[['economic_objective', 'technical_objective', 'social_objective']]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(
        df['economic_objective'],  # x
        df['technical_objective'],  # y
        df['social_objective'],     # z
        c='blue', alpha=0.7
    )

    ax.set_xlabel('Economic Objective')
    ax.set_ylabel('Technical Objective')
    ax.set_zlabel('Social Objective')
    plt.title('Pareto Front (3D)')

    plt.savefig(f'epsilon_sweep_3D_{config}_{charging_strategy}.png')
    plt.show()


    # Pair plot
    sns.pairplot(df)
    plt.suptitle('Pairwise Objective Trade-offs', y=1.02)
    plt.show()


    # Bubble plot
    plt.scatter(df['economic_objective'], df['technical_objective'],
                s=df['social_objective'], c=df['social_objective'], cmap='viridis', alpha=0.6)
    plt.xlabel('Economic')
    plt.ylabel('Technical')
    plt.title('2D Trade-off with Social as Bubble Size/Color')
    plt.colorbar(label='Social Objective')

    plt.savefig(f'2D_bubble_plot_{config}_{charging_strategy}.png')
    plt.show()




