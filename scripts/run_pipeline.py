from scripts.execute_models import execute_models
from scripts.analyse_results import analyse_results
from src.config import params
from pprint import pprint


def main():
    version = 'avgdist25km_without_f_fair'

    configurations = [
        'config_1',
        # 'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        'uncoordinated',
        'opportunistic',
        'flexible',
    ]

    execute_models(version, configurations, charging_strategies)

    raw_metrics, formatted_metrics = analyse_results(version, configurations, charging_strategies, params.num_of_evs)

    print(formatted_metrics)


if __name__ == '__main__':
    main()
