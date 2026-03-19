import numpy as np
import pandas as pd
import itertools
from typing import Dict, Any, Tuple


def compare_payoff_tables(payoff_tables: Dict[str, Dict[str, Dict[str, float]]]):
    """
    Compare payoff tables computed from different lexicographic starting orders.

    Args:
        payoff_tables: dict keyed by 'order_name' (e.g. 'econ','tech','soc'), each value is a payoff table:
                       payoff_tables[order_name][primary_obj][objective] = value

    Returns:
        summary_by_primary: dict mapping primary_obj -> pandas.DataFrame with statistics across orders
        distances_by_primary: dict mapping primary_obj -> pandas.DataFrame of pairwise Euclidean distances
        overall_summary: pandas.DataFrame summarizing worst-case variability across primaries
    """
    orders = list(payoff_tables.keys())
    # gather set of primary objectives and set of objectives
    any_order = payoff_tables[orders[0]]
    primary_objs = list(any_order.keys())
    objectives = list(next(iter(next(iter(payoff_tables.values())).values())).keys())

    summary_by_primary = {}
    distances_by_primary = {}

    overall_rows = []

    for primary in primary_objs:
        # build a DataFrame where rows = orders, cols = objectives
        data = {}
        for order in orders:
            row = payoff_tables[order][primary]
            # ensure the same objective order
            data[order] = [row[obj] for obj in objectives]
        df = pd.DataFrame.from_dict(data, orient='index', columns=objectives)

        # Stats per objective across orders
        stats = pd.DataFrame(index=objectives)
        stats['min'] = df.min(axis=0)
        stats['max'] = df.max(axis=0)
        stats['range'] = stats['max'] - stats['min']
        # relative range: range divided by (|min| if not zero else 1) to avoid div by zero
        stats['rel_range'] = stats['range'] / stats['min'].replace(0, np.nan).abs()
        stats['std'] = df.std(axis=0)
        stats['cv'] = stats['std'] / stats['min'].replace(0, np.nan).abs()
        # percent change (max relative to min)
        stats['pct_change_%'] = (stats['range'] / stats['min'].replace(0, np.nan)) * 100

        # Pairwise distances between orders (Euclidean distance of objective vectors)
        vecs = df.values  # rows = orders
        dist_mat = np.zeros((len(orders), len(orders)))
        for i, j in itertools.product(range(len(orders)), range(len(orders))):
            dist_mat[i, j] = np.linalg.norm(vecs[i] - vecs[j])
        dist_df = pd.DataFrame(dist_mat, index=orders, columns=orders)

        # Add per-primary summary to outputs
        summary_by_primary[primary] = df  # raw table of values per order
        # but also keep stats for convenience
        summary_by_primary[f"{primary}_stats"] = stats
        distances_by_primary[primary] = dist_df

        # Overall summary row for this primary
        overall_rows.append({
            'primary': primary,
            'worst_obj': stats['rel_range'].idxmax() if stats['rel_range'].notna().any() else None,
            'max_rel_range': stats['rel_range'].max(),
            'max_pct_change_%': stats['pct_change_%'].max(),
            'euclid_max_distance_between_orders': dist_df.values.max()
        })

    overall_summary = pd.DataFrame(overall_rows).set_index('primary')

    # Print a readable summary
    print("\n=== Payoff Tables Comparison Summary ===")
    for primary in primary_objs:
        print(f"\n-- Primary objective: {primary} --")
        stats = summary_by_primary[f"{primary}_stats"]
        # show concise table: min, max, range, rel_range (pct)
        display_df = stats[['min', 'max', 'range', 'rel_range', 'pct_change_%', 'std']].copy()
        print(display_df.to_string(float_format=lambda x: f"{x:.4g}"))
        print("\nPairwise Euclidean distances between orders:")
        print(distances_by_primary[primary].to_string(float_format=lambda x: f"{x:.4g}"))

    print("\n=== Overall variability summary (per primary objective) ===")
    print(overall_summary.to_string(float_format=lambda x: f"{x:.4g}"))

    return summary_by_primary, distances_by_primary, overall_summary


# --------------------------------
# Example usage with payoff data
# --------------------------------
econ = {'economic': {'economic': 4015.106649625589,
                     'social': 1289.6064562430095,
                     'technical': 168.95429729271316},
        'social': {'economic': 17255.3883632152,
                   'social': 494.30831075458633,
                   'technical': 222.89165444503868},
        'technical': {'economic': 17217.392819682846,
                      'social': 1044.62540796988,
                      'technical': 163.3830737085036}}

tech = {'economic': {'economic': 4015.106649625589,
                     'social': 1289.6064562430095,
                     'technical': 168.95429729271316},
        'social': {'economic': 17259.13802005956,
                   'social': 494.30831075458633,
                   'technical': 220.11850636432982},
        'technical': {'economic': 17217.392819682846,
                      'social': 1044.62540796988,
                      'technical': 163.3830737085036}}

soc = {'economic': {'economic': 4015.106649625589,
                    'social': 804.2286966515329,
                    'technical': 182.03549688335636},
       'social': {'economic': 17259.13802005956,
                  'social': 494.30831075458633,
                  'technical': 220.11850636432982},
       'technical': {'economic': 17217.783324932294,
                     'social': 1044.6254079700877,
                     'technical': 163.3830737085036}}


payoff_orders = {
    'start_econ': {
        'economic': {'economic': 4015.106649625589, 'social': 1289.6064562430095, 'technical': 168.95429729271316},
        'social': {'economic': 17255.3883632152, 'social': 494.30831075458633, 'technical': 222.89165444503868},
        'technical': {'economic': 17217.392819682846, 'social': 1044.62540796988, 'technical': 163.3830737085036},
    },
    'start_tech': {
        'economic': {'economic': 4015.106649625589, 'social': 1289.6064562430095, 'technical': 168.95429729271316},
        'social': {'economic': 17259.13802005956, 'social': 494.30831075458633, 'technical': 220.11850636432982},
        'technical': {'economic': 17217.392819682846, 'social': 1044.62540796988, 'technical': 163.3830737085036},
    },
    'start_soc': {
        'economic': {'economic': 4015.106649625589, 'social': 804.2286966515329, 'technical': 182.03549688335636},
        'social': {'economic': 17259.13802005956, 'social': 494.30831075458633, 'technical': 220.11850636432982},
        'technical': {'economic': 17217.783324932294, 'social': 1044.6254079700877, 'technical': 163.3830737085036},
    }
}

# Run the diagnostic
summary_by_primary, distances_by_primary, overall_summary = compare_payoff_tables(payoff_orders)
