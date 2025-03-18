from src.utils.execute_model import run_model
from src.utils.model_results import compile_multiple_models_metrics
from src.utils.evaluation_metrics import EvaluationMetrics
from src.utils.plot_results import plot_p_ev, plot_agg_total_demand, plot_agg_p_ev, plot_ev_charging_schedule


def main():
    configurations = [
        # 'config_1',
        'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        # 'opportunistic',
        'flexible',
    ]

    models_metrics = {}
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

            # Run and solve model
            results = run_model(config, charging_strategy, mip_gap=mip_gap, time_limit=time_limit, verbose=verbose)

            # Compute evaluation metrics
            # metrics = EvaluationMetrics(results)
            # metrics.pprint()
            # formatted_metrics = metrics.format_metrics()
            #
            # # Collect metrics
            # models_metrics[f'{config}_{charging_strategy}'] = formatted_metrics

            # Plot results
            plot_p_ev(results)
            plot_agg_p_ev(results)
            plot_agg_total_demand(results)

            if charging_strategy == 'flexible':
                plot_ev_charging_schedule(results)

    # Compile models metrics
    # results_df = compile_multiple_models_metrics(models_metrics, filename='compiled_metrics_3.csv')
    # print(results_df)

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
