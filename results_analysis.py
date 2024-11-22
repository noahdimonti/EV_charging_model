import numpy as np
import pandas as pd
import pyomo.environ as pyo
import params
# import uncoordinated_scenario_1 as us1
import coordinated_scenario_1 as cs1
from ModelOutputs import ModelOutputs





# collect results
# Coordinated Scenario 1
def run_models(df_cost, df_power):
    for tariff in params.tariff_types_list:
        for num_of_evs in range(0, 5):
            avg_travel_distance = 40
            cs1_model = cs1.create_model(tariff, num_of_evs, avg_travel_distance)
            cs1.solve_model(cs1_model)
            cs1_df = cs1.get_results_df(cs1_model)

            # append information to the dataframe
            # df_cost[f'CS1_{tariff}_tariff_{num_of_evs}_EVs'] = cs1.get_cost_results(cs1_model, tariff, num_of_evs)
            # df_power[f'CS1_{tariff}_tariff_{num_of_evs}_EVs'] = cs1.get_power_results(cs1_model, cs1_df, num_of_evs)

            df_cost.loc[(len(df_cost.index))] = cs1.get_cost_results(cs1_model, tariff, num_of_evs)
            df_cost['Model Name'] = f'CS1_{tariff}_tariff_{num_of_evs}_EVs'


    print(f'\n================ Cost Analysis ================\n')
    print(df_cost)

    # print(f'\n================ Power Analysis ================\n')
    # print(df_power)
    #
    return df_cost, df_power


# model test drive
cs1_model = cs1.create_model('flat', 10, 20, 0.4)
cs1.solve_model(cs1_model)
print(pyo.value(cs1_model.P_EV_max) * params.P_EV_resolution_factor)
print([pyo.value(cs1_model.P_EV_max_selection[i]) for i in range(len(params.P_EV_max_list))])


def export_to_csv(df_cost, df_power):
    df_cost.to_csv('df_cost.csv')
    df_power.to_csv('df_power.csv')


def main():
    df_cost, df_power = create_empty_df()
    df_cost, df_power = run_models(df_cost, df_power)
    export_to_csv(df_cost, df_power)
    print(f'Saving to csv ...')

    return df_cost

# main()


# if __name__ == '__main__':
    # main()






