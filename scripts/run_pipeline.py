from scripts.execute_models import execute_models
from scripts.analyse_results import analyse_results
from src.config import params
from src.visualisation import plot_models_comparison
from pprint import pprint


def main(run_model: bool, analyse: bool, plot: bool):
    version = 'confpaper_complete_obj'

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

    if run_model:
        execute_models(version, configurations, charging_strategies)

    if analyse:
        raw_metrics, formatted_metrics = analyse_results(
            configurations,
            charging_strategies,
            version,
            params.num_of_evs
        )
        print(formatted_metrics)

    if plot:
        plot_models_comparison.demand_profiles(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )
        plot_models_comparison.soc_distribution(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )
        plot_models_comparison.users_cost_distribution(
            configurations,
            charging_strategies,
            version,
            save_img=True
        )


if __name__ == '__main__':
    main(
        run_model=True,
        analyse=True,
        plot=True
    )
