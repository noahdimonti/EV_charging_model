import pandas as pd
import pyomo.environ as pyo
import matplotlib.pyplot as plt
import assets
from src.config import params
from src.config import ev_params
from src.config import independent_variables
from src.utils import solve_model
from src.utils.evaluation_metrics import ModelResults
from pprint import pprint
from build_model import plot_results, iterate_models, run_model


def main():
    # config = 'config_2'
    # charging_strategy = 'flexible'
    # model = run_model(config, charging_strategy, time_limit=600)

    configs = [assets.CPConfig.CONFIG_2]
    charging_strategies = [
        assets.ChargingStrategy.OPPORTUNISTIC,
        assets.ChargingStrategy.FLEXIBLE,
    ]

    iterate_models(configs, charging_strategies, plot=True)

    # Display key results
    # model.num_cp.display()
    # model.p_cp_rated.display()
    #
    # if charging_strategy == 'flexible':
    #     model.num_charging_days.display()
    #
    # plot_results(model)

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