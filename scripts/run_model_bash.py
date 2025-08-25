from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.utils.argparser import get_parser
from pprint import pprint

def main(argv=None):
    parser = get_parser()

    args = parser.parse_args(argv)

    results = run_optimisation_model(
        config=args.config,
        charging_strategy=args.charging_strategy,
        version=args.version,
        verbose=True,
        mip_gap=args.mip_gap,
        time_limit=args.time_limit,
        thread_count=args.thread_count
    )

    print(f'\nSolution values:')
    pprint(results.objective_components)

if __name__ == '__main__':
    main()