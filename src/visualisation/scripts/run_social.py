from src.visualisation.datasets.social import (
    build_soc_df,
    build_wait_time_df,
    build_num_charging_days_df,
)
from src.visualisation.plots.social import (
    plot_soc_boxplot,
    plot_wait_time_boxplot,
    plot_num_charging_days,
)


def main():
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['uncoordinated', 'opportunistic', 'flexible']
    version = 'balanced'

    df_soc = build_soc_df(configurations, charging_strategies, version)
    plot_soc_boxplot(df_soc, version=version, save_img=True)

    df_wait = build_wait_time_df(configurations, charging_strategies, version)
    plot_wait_time_boxplot(df_wait, version=version, save_img=True, save_csv=True)

    df_days = build_num_charging_days_df(configurations, charging_strategies, version)
    plot_num_charging_days(df_days, version=version, save_img=True)


if __name__ == '__main__':
    main()