import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import configs
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from src.utils.evaluation_metrics import EvaluationMetrics
from pprint import pprint
from execute_model import run_model, analyse_results


def main():
    config = 'config_1'
    charging_strategy = 'opportunistic'

    configurations = [
        'config_1',
        # 'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        'opportunistic',
        'flexible',
    ]

    results = run_model(config, charging_strategy)
    analyse_results(results)

    # model_data.p_ev.display()
    # model_data.num_cp.display()

    # if config == 'config_3':
    #     model_data.num_ev_sharing_cp.display()
    #     model_data.ev_is_permanently_assigned_to_cp.display()

    # if charging_strategy == 'flexible':
    #     model_data.num_charging_days.display()

    # Display key results
    # model_data.num_cp.display()
    # model_data.p_cp_rated.display()

    # Display detailed results
    # model_data.p_grid.display()
    # model_data.p_household_load.display()
    # model_data.p_cp.display()
    # model_data.p_ev.display()
    # model_data.soc_ev.display()

    # model_data.p_daily_peak.display()
    # model_data.p_daily_avg.display()
    # model_data.delta_daily_peak_avg.display()


if __name__ == '__main__':
    main()
