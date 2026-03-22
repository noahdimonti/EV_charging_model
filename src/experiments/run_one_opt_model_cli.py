from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.pipelines.analyse_results import analyse_one_model
from src.pipelines.argparser import get_parser
from src.experiments.obj_weights_map import obj_weights_dict


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

    df_metrics = analyse_one_model(results)
    print(df_metrics)


if __name__ == '__main__':
    main(
        # [
        #     '-c', 'config_3',
        #     '-s', 'flexible',
        #     '-w', 'min_econ',
        #     '-v', 'min_econ',
        #     '-m', '5',
        # ]
    )
