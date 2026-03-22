from src.pipelines.analyse_results import analyse_one_model_from_file

def main():
    config = 'config_2'
    strategy = 'flexible'
    version = 'min_econ'

    analyse_one_model_from_file(config, strategy, version)


if __name__ == '__main__':
    main()