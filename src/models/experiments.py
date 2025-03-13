import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import configs
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from src.utils.evaluation_metrics import ModelResults
from pprint import pprint
from execute_model import plot_results, iterate_models, run


def main():
    config = 'config_2'
    charging_strategy = 'flexible'

    configurations = [
        'config_1',
        'config_2',
        'config_3',
    ]
    charging_strategies = [
        'opportunistic',
        'flexible',
    ]

    # iterate_models(configurations, charging_strategies)

    model = run(config, charging_strategy, time_limit=10, mip_gap=8, save_results=True)
    # model.p_ev.display()
    # model.num_cp.display()

    # if config == 'config_3':
    #     model.num_ev_sharing_cp.display()
    #     model.ev_is_permanently_assigned_to_cp.display()

    # if charging_strategy == 'flexible':
    #     model.num_charging_days.display()

    # Display key results
    # model.num_cp.display()
    # model.p_cp_rated.display()

    # Display detailed results
    # model.p_grid.display()
    # model.p_household_load.display()
    # model.p_cp.display()
    # model.p_ev.display()
    # model.soc_ev.display()

    # model.p_daily_peak.display()
    # model.p_daily_avg.display()
    # model.delta_daily_peak_avg.display()


if __name__ == '__main__':
    main()
