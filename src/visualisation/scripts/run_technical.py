from src.visualisation.datasets.technical import (
    build_dso_metrics_df,
    build_objective_dso_metrics_df,
    build_p_ev_df,
    save_dso_metrics_df
)
from src.visualisation.plots.technical import (
    plot_num_ev_charging,
)


def main():
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['uncoordinated', 'opportunistic', 'flexible']

    version = 'balanced'

    # =========================
    # TECHNICAL: DSO METRICS
    # =========================
    df_models = build_dso_metrics_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
    )

    save_dso_metrics_df(
        df=df_models,
        filename=f'dso_metrics_{version}_models_comparison.csv',
    )

    print('\nDSO Metrics (Models Comparison):\n')
    print(df_models)

    # =========================
    # TECHNICAL: EV CHARGING ACTIVITY
    # =========================
    config = 'config_1'
    charging_strategies = ['opportunistic', 'flexible']

    df_p_ev = build_p_ev_df(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
    )

    plot_num_ev_charging(
        df=df_p_ev,
        config=config,
        charging_strategies=charging_strategies,
        version=version,
        save_img=True,
    )

    print('\nEV Charging Activity Data:\n')
    print(df_p_ev.head())


if __name__ == '__main__':
    main()