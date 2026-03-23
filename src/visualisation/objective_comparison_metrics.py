import numpy as np


def calculate_gini(values: np.ndarray) -> float:
    values = np.asarray(values).flatten()
    n = len(values)
    mean_value = np.mean(values)

    if mean_value == 0:
        return 0.0

    total_diff_sum = 0.0
    for i in range(n):
        for j in range(n):
            total_diff_sum += abs(values[i] - values[j])

    return total_diff_sum / (2 * (n ** 2) * mean_value)
