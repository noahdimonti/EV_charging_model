from src.pipelines.analyse_results import analyse_one_model_from_file

def main():
    config = 'config_2'
    strategy = 'opportunistic'
    version = 'balanced_sens_analysis_avgdist25km_min0.4_max0.6_cap35_60'
    # version = 'balanced'


    df = analyse_one_model_from_file(config, strategy, version)
    print(df)


if __name__ == '__main__':
    main()