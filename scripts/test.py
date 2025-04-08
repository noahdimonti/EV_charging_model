import pandas as pd
import matplotlib.pyplot as plt
import os

pd.set_option('display.max_columns', None)

# root = os.path.dirname(os.path.abspath(__file__))
# filepath = root / '../../data/outputs/csv/compiled_metrics_without_ffair_objective.csv'
# filepath = filepath.resolve()
# print(filepath)



print(pd.read_csv('../../data/outputs/csv/compiled_metrics_without_ffair_objective.csv'))
print(pd.read_csv('../../data/outputs/csv/compiled_metrics_new.csv'))
print(pd.read_csv('../../data/outputs/csv/compiled_metrics_test.csv'))


# Example data
categories = ['A', 'B', 'C', 'D']
values = [10, 20, 15, 25]

plt.figure(figsize=(8, 5))  # Set figure size
plt.bar(categories, values, color='slateblue')
# darkseagreen
# slateblue

plt.xlabel("Categories")
plt.ylabel("Values")
plt.title("Bar Chart Example")
plt.grid(axis='y', linestyle='--', alpha=0.4)  # Add grid lines on y-axis

# plt.savefig(f'../test.png', dpi=300)
#
# plt.show()
