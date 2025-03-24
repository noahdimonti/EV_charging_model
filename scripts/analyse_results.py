import pandas as pd
import pickle
from src.utils.evaluation_metrics import EvaluationMetrics
from src.utils.evaluation_metrics import compile_multiple_models_metrics
from src.visualisation.plot_results import plot_p_ev, plot_agg_p_ev, plot_agg_total_demand, plot_ev_charging_schedule


def main():
    pd.set_option('display.max_columns', None)

    num_ev = 5
    version = 'test'

    # plot = True
    plot = False

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
        for strategy in charging_strategies:
            filename = f'../../reports/pkl/{config}_{strategy}_{num_ev}EVs_7days.pkl'

            with open(filename, 'rb') as f:
                results = pickle.load(f)

            # Compute evaluation metrics
            metrics = EvaluationMetrics(results)
            formatted_metrics = metrics.format_metrics()

            # Collect metrics
            models_metrics[f'{config}_{strategy}'] = formatted_metrics

            # Plot results
            if plot:
                plot_p_ev(results)
                plot_agg_p_ev(results)
                plot_agg_total_demand(results)

                if strategy == 'flexible':
                    plot_ev_charging_schedule(results)

    # Compile models metrics
    metrics_filename = 'compiled_metrics_new.csv'
    results_df = compile_multiple_models_metrics(models_metrics, filename=metrics_filename)
    print(results_df)


if __name__ == '__main__':
    main()
