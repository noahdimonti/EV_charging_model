import pandas as pd

metrics_old = pd.read_csv('../../reports/csv/compiled_metrics.csv')
metrics_new = pd.read_csv('../../reports/csv/compiled_metrics_rev.csv')


print(metrics_old)
print(metrics_new)