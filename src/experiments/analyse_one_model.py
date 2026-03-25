from src.pipelines.analyse_results import analyse_one_model_from_file

def main():
    config = 'config_2'
    strategy = 'opportunistic'
    version = 'thread16'


    df = analyse_one_model_from_file(config, strategy, version)
    print(df)


if __name__ == '__main__':
    main()