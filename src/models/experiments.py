from src.utils.execute_model import run_model
from src.utils.model_results import compile_metrics_from_multiple_models
from src.utils.evaluation_metrics import EvaluationMetrics


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

    models_metrics = {}
    for config in configurations:
        for charging_strategy in charging_strategies:
            # Run and solve model
            results = run_model(config, charging_strategy)

            # Compute evaluation metrics
            metrics = EvaluationMetrics(results).format_metrics()

            # Collect metrics
            models_metrics[f'{config}_{charging_strategy}'] = metrics

    # Compile models metrics
    results_df = compile_metrics_from_multiple_models(models_metrics)
    print(results_df)

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
