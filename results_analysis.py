import pandas as pd
import params
# import uncoordinated_scenario_1 as us1
import coordinated_scenario_1 as cs1

cost_metrics_list = [
    'Tariff type',
    'Total optimal cost ($)',
    'Investment & maintenance cost ($)',
    'Total household load cost ($)',
    'Total EV charging cost ($)',
    'Grid import cost ($)',
    'Other costs ($)',  # daily supply charge and continuity penalty costs
    'Average EV charging cost ($)'
]

power_metrics_list = [
    'Number of households',
    'Number of EVs',
    'Number of CPs',
    'Max charging power (kW)',
    'Peak EV load (kW)',
    'Peak total demand (kW)',
    'Peak grid import (kW)',
    'Average daily peak (kW)',
    'Peak-to-average power ratio (PAPR)'
]

# initialise empty dataframes
df_cost = pd.DataFrame(columns=['cost_information'])
df_cost['cost_information'] = cost_metrics_list

df_power = pd.DataFrame(columns=['power_information'])
df_power['power_information'] = power_metrics_list
print(df_cost)
print(df_power)


# collect results

# Coordinated Scenario 1
for tariff in params.tariff_types_list:
    num_of_evs = 50
    avg_travel_distance = 40
    cs1_model = cs1.create_model(tariff, num_of_evs, avg_travel_distance)
    cs1.solve_model(cs1_model)
    cs1_df = cs1.get_results_df(cs1_model)
    df_cost[f'CS1_{tariff}_tariff'] = cs1.get_cost_results(cs1_model, tariff, num_of_evs)
    df_power[f'CS1_{tariff}_tariff'] = cs1.get_power_results(cs1_model, cs1_df, num_of_evs)

print(f'\n================ Cost Analysis ================\n')
print(df_cost)

print(f'\n================ Power Analysis ================\n')
print(df_power)


for num_of_evs in params.num_of_evs_list:
    pass








