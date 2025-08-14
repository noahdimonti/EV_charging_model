from augmecon_algorithm import augmecon_sweep
from get_payoff_tables import payoff_tables
from src.models.utils.log_model_info import log_with_runtime, print_runtime
from pprint import pprint


def main():
    config = 'config_1'
    charging_strategy = 'opportunistic'
    version = 'augmecon_test'

    primary_obj = 'social'
    grid_points = 3

    payoff = payoff_tables.get(f'{config}_{charging_strategy}')

    (pareto_sols, infeasible_records), runtime = log_with_runtime(
        f'Starting AUGMECON Sweep on {config}_{charging_strategy} model',
        augmecon_sweep,
        payoff_table=payoff,
        primary_obj=primary_obj,
        grid_points=grid_points,
        config=config,
        charging_strategy=charging_strategy,
        version=version,
    )

    print_runtime(
        finished_label=f'Finished running',
        runtime=runtime
    )


    print(f'Pareto solutions:')
    pprint(pareto_sols)

    print(f'Infeasible:')
    pprint(infeasible_records)





if __name__ == '__main__':
    main()