from augmecon_algorithm import *


def main():
    config = 'config_2'
    charging_strategy = 'flexible'
    version = 'augmecon_test'

    objectives_priority = [
        'social',
        'economic',
        'technical'
    ]

    payoff = build_payoff_table(
        objectives=objectives_priority,
        config=config,
        charging_strategy=charging_strategy,
        version=version,
    )

    pprint(payoff, sort_dicts=False)


if __name__ == '__main__':
    main()