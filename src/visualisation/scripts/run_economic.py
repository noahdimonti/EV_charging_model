from src.visualisation.datasets.economic import build_num_cp_df


def main():
    configurations = ['config_1', 'config_2', 'config_3']
    charging_strategies = ['uncoordinated', 'opportunistic', 'flexible']
    version = 'balanced'

    df_num_cp = build_num_cp_df(configurations, charging_strategies, version)
    print(df_num_cp)


if __name__ == '__main__':
    main()