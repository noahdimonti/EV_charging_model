from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.pipelines.analyse_results import analyse_one_model_formatted
from src.pipelines.argparser import get_parser
from src.experiments.obj_weights_map import obj_weights_dict
from src.config.params import (
    avg_travel_distance,
    min_initial_soc,
    max_initial_soc,
    ev_capacity_range_low,
    ev_capacity_range_high
)


def main(argv=None):
    parser = get_parser()

    args = parser.parse_args(argv)

    results = run_optimisation_model(
        config=args.config,
        charging_strategy=args.charging_strategy,
        version=args.version,
        obj_weights=obj_weights_dict[args.obj_weights_type],
        verbose=True,
        mip_gap=args.mip_gap,
        time_limit=args.time_limit,
        thread_count=args.thread_count
    )

    df_metrics = analyse_one_model_formatted(results)
    print(df_metrics)


if __name__ == '__main__':
    # version = (f'balanced_sens_analysis_avgdist{avg_travel_distance}km_'
    #            f'min{min_initial_soc}_max{max_initial_soc}_'
    #            f'cap{ev_capacity_range_low}_{ev_capacity_range_high}')

    main(
        # [
        #     '-c', 'config_2',
        #     '-s', 'opportunistic',
        #     '-w', 'balanced',
        #     '-v', version,
        #     '-m', '3',
        #     '-t', '360',
        #     '-n', '1',
        #
        # ]
    )
