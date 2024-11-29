import pandas as pd
import numpy as np
import pyomo.environ as pyo
import plotly.graph_objects as go
from pprint import pprint

import output_collection
import params
import solve_model

from models import uncoordinated_scenario_1 as us1
from models import coordinated_scenario_1 as cs1


def generate_results(
    model_frameworks: dict,
    tariff_types: list[str],
    num_of_evs_list: list[int],
    avg_travel_distance_list: list[float],
    min_soc_list: list[float],
    output_csv_path: str = 'results_data/model_results.csv'
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

    Returns:
        pd.DataFrame: Combined DataFrame of all model results.
    """
    # Create a list to store DataFrame results from all model runs
    all_model_dfs = []

    # Iterate through each combination of inputs
    for model_framework, model_type in model_frameworks.items():
        for tariff_type in tariff_types:
            for num_of_evs in num_of_evs_list:
                for avg_travel_distance in avg_travel_distance_list:
                    for min_soc in min_soc_list:
                        # Generate and solve the model instance
                        model_instance = model_framework.create_model_instance(
                            tariff_type, num_of_evs, avg_travel_distance, min_soc
                        )

                        try:
                            if model_type == 'coordinated':
                                solve_model.solve_optimisation_model(model_instance)
                            elif model_type == 'uncoordinated':
                                solve_model.simulate_uncoordinated_model(model_instance)

                            # Collect outputs and convert them to a DataFrame
                            model_output = output_collection.collect_model_outputs(
                                model_instance, model_type, tariff_type, num_of_evs, avg_travel_distance, min_soc
                            )

                            # print(f'{model_type} ev load')
                            # print(f'ev load: {model_output.ev_load}')
                            print(f'total ev load: {model_output.total_ev_load}')
                            print(f'peak ev load: {model_output.peak_ev_load}')
                            print(f'p ev max: {model_output.max_charging_power}')

                            fig = go.Figure()

                            fig.add_trace(go.Scatter(x=params.timestamps, y=model_output.ev_load, name='EV Load'))
                            fig.add_trace(go.Scatter(x=params.timestamps, y=[model_output.peak_ev_load for _ in range(len(params.timestamps))], name='Peak EV Load'))
                            fig.update_layout(title=f'EV Load - {model_output.model_name}',
                                              xaxis_title=f'Timestamp',
                                              yaxis_title=f'EV Load (kW)',)
                            fig.show()


                            output_df = model_output.to_dataframe()

                            # Append DataFrame to the list
                            all_model_dfs.append(output_df)

                        except ValueError as e:
                            print(f'{model_instance.name} model might be infeasible.'
                                  f'\nError detail: {e}.')

    # Combine all DataFrames horizontally (axis=1)
    combined_df = pd.concat(all_model_dfs, axis=1)

    # Save the combined DataFrame to a CSV file
    combined_df.to_csv(output_csv_path, index=True)
    print(f'Results saved to {output_csv_path}\n')

    return combined_df


# Model variables
models = {
    # us1: 'uncoordinated',
    cs1: 'coordinated',
}
tariffs = ['flat', 'tou']
num_evs = [50, 100]
avg_dist = [15, 25, 35]
min_soc = [0.4, 0.6, 0.8]

# Generate and print results
# df = generate_results(models, tariffs, num_evs, avg_dist, min_soc)
# print(df)




num_ev = [100]
avg_distance = [30]
minim_soc = [0.9]

df = generate_results(models, ['flat'], num_ev, avg_distance, minim_soc)
print(df)


# model_2 = cs1.create_model_instance('flat', num_ev, avg_distance, minim_soc)
# solve_model.solve_optimisation_model(model_2)
#
#
# for ev_id in range(40, 45):
#     fig = go.Figure()
#
#     fig.add_trace(go.Scatter(x=params.timestamps, y=[pyo.value(model_2.P_EV[ev_id, t]) for t in model_2.TIME]))
#     fig.update_layout(title=f'EV Load - EV_ID{ev_id}',
#                       xaxis_title=f'Timestamp',
#                       yaxis_title=f'EV Load (kW)',)
#     fig.show()


# model_2.SOC_EV.display()
# model_2.P_EV.display()
# model_2.soc_min_priority_constraint.display()
# model_2.EV_at_home_status.display()
# # model_2.obj_function.display()
# model_2.P_EV_max.display()
# model_2.display()
