import numpy as np
import pandas as pd
import pyomo.environ as pyo
from pprint import pprint
import params
# import uncoordinated_scenario_1 as us1
import coordinated_scenario_1 as cs1


def collect_results(
    model_frameworks: list,
    tariff_types: list[str],
    num_of_evs_list: list[int],
    avg_travel_distance_list: list[float],
    min_soc_list: list[float],
    output_csv_path: str = "model_results.csv"
):
    """
    Collects results from multiple model runs, compiles them into a single DataFrame,
    and saves the results to a CSV file.

    Parameters:
        model_frameworks (list): List of model frameworks to evaluate.
        tariff_types (list[str]): List of tariff types to use in models.
        num_of_evs_list (list[int]): List of EV quantities to test.
        avg_travel_distance_list (list[float]): List of average travel distances (in km).
        min_soc_list (list[float]): List of minimum SOC requirements (as fractions).
        output_csv_path (str): Path to save the resulting CSV file. Default is 'model_results.csv'.

    Returns:
        pd.DataFrame: Combined DataFrame of all model results.
    """
    # Create a list to store DataFrame results from all model runs
    all_model_dfs = []

    # Iterate through each combination of inputs
    for model_framework in model_frameworks:
        for tariff_type in tariff_types:
            for num_of_evs in num_of_evs_list:
                for avg_travel_distance in avg_travel_distance_list:
                    for min_soc in min_soc_list:
                        # Generate and solve the model instance
                        model_instance = model_framework.create_model_instance(
                            tariff_type, num_of_evs, avg_travel_distance, min_soc
                        )
                        model_framework.solve_model(model_instance, verbose=True)

                        # Collect outputs and convert them to a DataFrame
                        model_output = model_framework.collect_model_outputs(
                            model_instance, tariff_type, num_of_evs, avg_travel_distance, min_soc
                        )
                        output_df = model_output.to_dataframe()

                        # Append DataFrame to the list
                        all_model_dfs.append(output_df)

    # Combine all DataFrames horizontally (axis=1)
    combined_df = pd.concat(all_model_dfs, axis=1)

    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_csv_path, index=True)
    print(f"Results saved to {output_csv_path}")

    return combined_df


models = [cs1]
tariffs = ['flat', 'tou']
num_evs = [100]
avg_dist = [20]
min_soc = [0.3, 0.4]

df = collect_results(models, tariffs, num_evs, avg_dist, min_soc)
print(df)





