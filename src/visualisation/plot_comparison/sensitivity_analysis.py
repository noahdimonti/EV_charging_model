import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

from src.visualisation import io, style
from src.config import params


def get_filepath(version: str, min_soc: float, max_soc: float, cap: str, avg_dist: int):
    file_prefix = f'raw_values_compiled_metrics_{params.num_of_evs}EVs_{params.num_of_days}days_{version}'
    file_parameters = f'{min_soc}min_{max_soc}max_cap{cap}_{avg_dist}km.csv'
    file_path = "_".join([file_prefix, file_parameters])

    return file_path


def get_df(params_comb: list[dict]):
    all_data = []

    folder = os.path.join(params.compiled_metrics_folder_path, 'sensitivity_analysis')

    metrics_keep = [
        'num_cp',
        'p_cp_rated',
        'p_peak_increase',
        'papr',
        'avg_soc_t_dep_percent',
        'lowest_soc'
    ]

    for parameter in params_comb:
        filepath = get_filepath(
            version,
            parameter['min_soc'],
            parameter['max_soc'],
            parameter['cap'],
            parameter['avg_dist']
        )
        file = os.path.join(folder, filepath)

        df = pd.read_csv(file, index_col=0).T

        df = df[metrics_keep]

        # store filename (model case)
        df['model_case'] = filepath.replace('.csv', '')

        all_data.append(df)

    df_all = pd.concat(all_data, ignore_index=True)

    soc_vals = df_all['model_case'].str.extract(r'(\d\.\d)min_(\d\.\d)max')

    df_all['soc_range'] = (
            (soc_vals[0].astype(float) * 100).astype(int).astype(str)
            + '-'
            + (soc_vals[1].astype(float) * 100).astype(int).astype(str)
            + '%'
    )

    df_all['capacity'] = (
            df_all['model_case']
            .str.extract(r'cap(\d+-\d+)')[0]
            + ' kWh'
    )

    df_all['distance'] = (
            df_all['model_case']
            .str.extract(r'(\d+)km')[0]
            + ' km'
    )

    df_all = df_all[
        [
            'model_case',
            'soc_range',
            'capacity',
            'distance',
            'p_peak_increase',
            'papr',
            'num_cp',
            'p_cp_rated',
            'avg_soc_t_dep_percent',
            'lowest_soc'
        ]
    ]

    df_all = df_all.set_index('model_case')

    return df_all


def plot_sensitivity(df: pd.DataFrame, metrics: list[str], y_labels: list[str], x_col: str, title: str, filename: str, order: list[str]):
    sns.set_theme(style='whitegrid', context='paper')

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    axes = axes.flatten()

    df = df.copy()
    df[x_col] = pd.Categorical(df[x_col], categories=order, ordered=True)
    df = df.sort_values(x_col)

    ylims = {
        'num_cp': (0, 10),
        'papr': (2.2, 2.6),
        'avg_soc_t_dep_percent': (50, 100),
        'lowest_soc': (50, 100)
    }

    offsets = {
        'num_cp': 0.5,
        'papr': 0.02,
        'avg_soc_t_dep_percent': 3,
        'lowest_soc': 3
    }

    baseline = order[1]
    baseline_df = df[df[x_col] == baseline]

    for i, metric in enumerate(metrics):
        sns.lineplot(
            data=df,
            x=x_col,
            y=metric,
            marker='o',
            linewidth=2,
            color='#4C72B0',
            ax=axes[i]
        )

        axes[i].scatter(
            baseline_df[x_col],
            baseline_df[metric],
            color='#D62728',
            s=120,
            zorder=5
        )

        axes[i].set_xlabel('')
        axes[i].set_ylabel('')
        axes[i].set_title(
            y_labels[metric],
            fontsize=15,
            fontweight='bold',
            pad=12
        )
        axes[i].margins(x=0.1)
        axes[i].set_ylim(ylims[metric])

        axes[i].tick_params(
            axis='both',
            labelsize=14,
        )

        for label in axes[i].get_xticklabels():
            label.set_fontweight('bold')

        for label in axes[i].get_yticklabels():
            label.set_fontweight('bold')

        # Set annotation on datapoints
        for x, y in zip(df[x_col], df[metric]):
            if metric == 'num_cp':
                label = f'{int(y)} CP'
            else:
                label = f'{y:.2f}'

            axes[i].text(
                x,
                y + offsets[metric],
                label,
                ha='center',
                fontsize=11,
                fontweight='bold'
            )

    fig.suptitle(
        title,
        fontsize=18,
        fontweight='bold',
    )

    plt.tight_layout(pad=2.5)

    filepath = os.path.join(params.plots_folder_path, filename)
    plt.savefig(filepath, dpi=300)
    plt.close()


if __name__ == '__main__':
    pd.set_option('display.max_columns', None)

    version = 'norm_w_sum'
    params_combination = [
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35-60', 'avg_dist': 25},  # Baseline
        {'min_soc': 0.2, 'max_soc': 0.4, 'cap': '35-60', 'avg_dist': 25},  # SOC init
        {'min_soc': 0.6, 'max_soc': 0.8, 'cap': '35-60', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '30-40', 'avg_dist': 25},  # Battery capacity
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '55-65', 'avg_dist': 25},
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35-60', 'avg_dist': 15},  # Avg travel distance
        {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35-60', 'avg_dist': 35},
    ]

    metrics = [
        'num_cp',
        'papr',
        'avg_soc_t_dep_percent',
        'lowest_soc'
    ]

    y_labels = {
        'num_cp': 'Number of charging points',
        'papr': 'Peak-to-average power ratio',
        'avg_soc_t_dep_percent': 'Average SOC at departure (%)',
        'lowest_soc': 'Lowest SOC at departure (%)'
    }

    df_all = get_df(params_combination)

    # Sensitivity to initial SOC
    df_soc = df_all[df_all['capacity'] == '35-60 kWh']
    df_soc = df_soc[df_soc['distance'] == '25 km']
    plot_sensitivity(
        df_soc,
        metrics,
        y_labels,
        'soc_range',
        'Sensitivity to initial SOC range',
        'soc_sensitivity.png',
        ['20-40%', '40-60%', '60-80%']
    )

    # Sensitivity to EV capacity
    df_cap = df_all[df_all['soc_range'] == '40-60%']
    df_cap = df_cap[df_cap['distance'] == '25 km']
    plot_sensitivity(
        df_cap,
        metrics,
        y_labels,
        'capacity',
        'Sensitivity to EV battery capacity',
        'capacity_sensitivity.png',
        ['30-40 kWh', '35-60 kWh', '55-65 kWh']
    )

    # Sensitivity to average travel distance
    df_dist = df_all[df_all['soc_range'] == '40-60%']
    df_dist = df_dist[df_dist['capacity'] == '35-60 kWh']
    plot_sensitivity(
        df_dist,
        metrics,
        y_labels,
        'distance',
        'Sensitivity to average travel distance',
        'distance_sensitivity.png',
        ['15 km', '25 km', '35 km']
    )