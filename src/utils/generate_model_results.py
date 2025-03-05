import pandas as pd
import warnings

import pyomo.environ as pyo

from src.config import params
from src.utils import output_collection, solve_model

from src.models import uncoordinated_scenario_1 as us1

from src.visualisation import plot_results

# Ignore warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)


def print_essential_stats(model_output):
    print(f'--- Essential Statistics ---')
    print(f'Total EV Load: {model_output.total_ev_load} kW')
    print(f'Peak EV Load: {model_output.peak_ev_load} kW')
    print(f'Max charging power: {model_output.max_charging_power} kW')


def generate_results(
        model_frameworks: dict,
        tariff_types: list[str],
        num_of_evs_list: list[int],
        avg_travel_distance_list: list[float],
        min_soc_list: list[float],
        output_csv_path: str,
        plot: bool = False
):
    """
    Collects results from multiple model runs, compiles them into a single DataFrame,
    and saves the results to a CSV file.

    Parameters:
        model_frameworks (dict): keys: model frameworks to evaluate, values: type of model (coordinated or uncoordinated).
        tariff_types (list[str]): List of tariff types to use in models.
        num_of_evs_list (list[int]): List of EV quantities to test.
        avg_travel_distance_list (list[float]): List of average travel distances (in km).
        min_soc_list (list[float]): List of minimum SOC requirements (as fractions).
        output_csv_path (str): Path to save the resulting CSV file. Default is 'model_results'.
        plot (bool): Whether to plot the results.

    """
    # Create a list to store DataFrame results from all model runs
    all_model_dfs = []

    # Dictionary to store P_EV_max from coordinated models
    p_ev_max_dict = {}

    # Iterate through each combination of inputs
    for model_framework, model_type in model_frameworks.items():
        for tariff_type in tariff_types:
            for num_of_evs in num_of_evs_list:
                for avg_travel_distance in avg_travel_distance_list:
                    for min_soc in min_soc_list:
                        # Generate and solve the model instance
                        try:
                            # Create model_instance variable
                            model_instance = None

                            if model_type == 'coordinated':
                                # Create and solve coordinated model
                                model_instance = model_framework.create_optimisation_model_instance(
                                    tariff_type, num_of_evs, avg_travel_distance, min_soc
                                )
                                solve_model.solve_optimisation_model(model_instance)

                                # Store P_EV_max for later use
                                p_ev_max = pyo.value(model_instance.p_cp_max) * params.P_EV_resolution_factor
                                p_ev_max_dict[(tariff_type, num_of_evs, avg_travel_distance, min_soc)] = p_ev_max

                            elif model_type == 'uncoordinated':
                                # Retrieve P_EV_max from the coordinated model
                                if (tariff_type, num_of_evs, avg_travel_distance, min_soc) not in p_ev_max_dict:
                                    raise ValueError(
                                        f'P_EV_max is not available for coordinated model with parameters:\n'
                                        f'tariff_type={tariff_type}, num_of_evs={num_of_evs}, '
                                        f'avg_travel_distance={avg_travel_distance}, min_soc={min_soc}')

                                p_ev_max = p_ev_max_dict[(tariff_type, num_of_evs, avg_travel_distance, min_soc)]

                                # Create and simulate the uncoordinated model
                                model_instance = model_framework.simulate_uncoordinated_model(
                                    p_ev_max, tariff_type, num_of_evs, avg_travel_distance, min_soc
                                )
                                solve_model.simulate_uncoordinated_model(model_instance)

                            # Collect outputs and convert them to a DataFrame
                            model_output = output_collection.collect_model_outputs(
                                model_instance, model_type, tariff_type, num_of_evs, avg_travel_distance, min_soc
                            )

                            # print essential statistics and plot results
                            print_essential_stats(model_output)

                            # plot the output
                            if plot:
                                plot_results.plot_results(model_output)

                            # Convert model_output object into a dataframe
                            output_df = model_output.to_dataframe()

                            # Append DataFrame to the list
                            all_model_dfs.append(output_df)

                        except ValueError as e:
                            print(f'Error processing {model_type} model with parameters:\n'
                                  f'tariff_type={tariff_type}, num_of_evs={num_of_evs}, '
                                  f'avg_travel_distance={avg_travel_distance}, min_soc={min_soc}.\n'
                                  f'Error detail: {e}')

    # Combine all DataFrames horizontally (axis=1)
    combined_df = pd.concat(all_model_dfs, axis=1)

    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_csv_path, index=True)
    print(f'---------------------------------------------------------\n')
    print(f'{params.GREEN}Simulation is completed.{params.RESET}')
    print(f'Results saved to {output_csv_path}\n')
    print(f'---------------------------------------------------------\n')

    return combined_df


# Model variables
models = {
    # cs1: 'coordinated',
    us1: 'uncoordinated'
}
tariffs = [
    'flat',
    # 'tou'
]
num_evs = [
    50,
    # 100
]
avg_dist = [
    # 15,
    # 25,
    35
]
min_soc = [
    0.4,
    # 0.6,
    # 0.8
]



# # Generate and print results
# df = generate_results(models, tariffs, num_evs, avg_dist, min_soc, output_csv_path=f'reports/simulation_results.csv')
# print(df)



