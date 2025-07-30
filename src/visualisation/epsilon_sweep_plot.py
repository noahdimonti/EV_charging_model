import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from src.config import params
import os

filename = 'scripts/epsilon_constraint/epsilon_sweep.csv'
filepath = os.path.join(params.project_root, filename)

df = pd.read_csv(filepath)
df = df[['economic_objective', 'technical_objective', 'social_objective']]
print(df)

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

plt.savefig('epsilon_sweep_3D.png')
# plt.show()

# import seaborn as sns
# import matplotlib.pyplot as plt
#
# sns.pairplot(df)
# plt.suptitle('Pairwise Objective Trade-offs', y=1.02)
# plt.show()





