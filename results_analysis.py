import pandas as pd
import params
# import uncoordinated_scenario_1
import coordinated_scenario_1

coordinated_scenario_1.solve_model()

general_information = [
    'Number of households',
    'Number of EVs',
    'Number of CPs',
    'Max charging power'
]

cost_metrics_list = [
    'Tariff type',
    'Total optimal cost',
    'Investment & maintenance cost',
    'Total household load cost',
    'Total EV charging cost',
    'Other costs',  # daily supply charge and continuity penalty costs
    'Average EV charging cost'
]

power_metrics_list = [
    'Peak EV demand',
    'Peak power',
    'Peak grid import',
    'Average daily peak',
    'Peak-to-average power ratio (PAPR)'
]

df_general = pd.DataFrame(columns=['General Information'])
df_general['General Information'] = general_information

df_cost = pd.DataFrame(columns=['Cost Information'])
df_cost['Cost Information'] = cost_metrics_list

df_power = pd.DataFrame(columns=['Power Information'])
df_power['Power Information'] = power_metrics_list



