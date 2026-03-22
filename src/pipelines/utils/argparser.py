import argparse

from pygments.lexer import default


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str,
                        help="Configuration (e.g., config_1, config_2, config_3)")
    parser.add_argument('-s', '--charging_strategy', type=str,
                        help="Charging strategy (e.g., opportunistic, flexible)")
    parser.add_argument('-w', '--obj_weights_type', type=str,
                        help="Objective weights type (e.g. balanced, min_econ, econ_tech, etc)")
    parser.add_argument('-v', '--version', type=str, default='test',
                        help="Model or experiment version")

    parser.add_argument('-t', '--time_limit', type=int, default=30,  # in minutes
                        help="Solver time limit in minutes")
    parser.add_argument('-m', '--mip_gap', type=float, default=1,
                        help="MIP gap in percentage")
    parser.add_argument('-n', '--thread_count', type=int, default=16,
                        help="Number of solver threads")
    return parser