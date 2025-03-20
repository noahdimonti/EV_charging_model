from src.utils.execute_model import run_model


def main():
    configurations = [
        'config_1',
        # 'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        'opportunistic',
        'flexible',
    ]

    for config in configurations:
        for charging_strategy in charging_strategies:
            # Set mip gap and time limit
            mip_gap = None
            time_limit = None
            verbose = False

            if charging_strategy == 'opportunistic' and config != 'config_1':
                verbose = True
                mip_gap = 0.5
                time_limit = 60 * 15
            elif charging_strategy == 'flexible' and config != 'config_1':
                verbose = True
                mip_gap = 0.9
                time_limit = 60 * 30

            # Run, solve, and save solved model
            run_model(config, charging_strategy, mip_gap=mip_gap, time_limit=time_limit, verbose=verbose)


if __name__ == '__main__':
    main()
