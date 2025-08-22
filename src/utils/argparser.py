import argparse

def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str,
                        help="Configuration (e.g., config_1, config_2, config_3)")
    parser.add_argument('-s', '--charging_strategy', type=str,
                        help="Charging strategy (e.g., opportunistic, flexible)")
    parser.add_argument('-v', '--version', type=str, default='augmecon',
                        help="Algorithm version")

    parser.add_argument('-t', '--time_limit', type=int, default=30,
                        help="Solver time limit in minutes")
    parser.add_argument('-n', '--thread_count', type=int, default=16,
                        help="Number of solver threads")

    parser.add_argument('-o', '--primary_obj', type=str, default='social',
                        help="Primary objective (e.g., social, economic, technical)")
    parser.add_argument('-g', '--grid_points', type=int, default=20,
                        help="Number of grid points")

    return parser