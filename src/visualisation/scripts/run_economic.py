from src.visualisation.datasets.economic import build_num_cp_df
from src.visualisation.plots.economic import plot_num_cp


def main():
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['uncoordinated', 'opportunistic', 'flexible']
    version = 'balanced'

    df_num_cp = build_num_cp_df(configurations, charging_strategies, version)
    plot_num_cp(df_num_cp, version=version, save_img=True)


if __name__ == '__main__':
    main()