import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import data_cleaning as dc
import pickle
import os
from pprint import pprint
import params

# files and folders path
vista_raw_path = '/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling Data/Potential Datasets/vista/T_VISTA1218_V1.csv'
work_ev_path = ('/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling '
                'Data/Potential Datasets/vista/VISTA_Time_HomeDeAr_WorkVehicle.csv')
casual_ev_path = ('/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling '
                  'Data/Potential Datasets/vista/VISTA_Time_HomeDeAr_CasualVehicle.csv')
ev_model_path = '/Users/noahdimonti/Developer/PycharmProjects/EV_model_test/'

# initialise and clean work_ev data (for weekdays)
work_ev = pd.read_csv(work_ev_path)
work_ev = dc.clean_raw_data(work_ev)
work_ev = dc.convert_to_timestamp(df=work_ev, date_time=params.start_date_time)
work_ev = dc.remove_outliers(work_ev)

# initialise and clean casual_ev data (for weekends)
# clean data
casual_ev = pd.read_csv(casual_ev_path)
casual_ev.rename(columns={'Three _2nd_ARRTIME': 'Three_2nd_ARRTIME',
                          'Three _2nd_DEPTIME': 'Three_2nd_DEPTIME'}, inplace=True)
casual_ev = dc.clean_raw_data(casual_ev)
casual_ev = dc.convert_to_timestamp(df=casual_ev, date_time=params.start_date_time)

# rearrange columns
casual_ev_once = casual_ev[['Once_DEPTIME', 'Once_ARRTIME']]
casual_ev_twice = casual_ev[['Twice_1st_DEPTIME', 'Twice_1st_ARRTIME', 'Twice_2nd_DEPTIME', 'Twice_2nd_ARRTIME']]
casual_ev_three = casual_ev[['Three_1st_DEPTIME', 'Three_1st_ARRTIME', 'Three_2nd_DEPTIME', 'Three_2nd_ARRTIME', 'Three_3rd_DEPTIME', 'Three_3rd_ARRTIME']]

# create a list of casual ev dataframes
casual_ev_df_list = [casual_ev_once, casual_ev_twice, casual_ev_three]
for i in range(len(casual_ev_df_list)):
    casual_ev_df_list[i] = dc.remove_outliers(casual_ev_df_list[i])


# create 7 days EV at home status profile
class ElectricVehicle:
    def __init__(self):
        self.at_home_status = pd.DataFrame
        self.t_arr = []
        self.soc_t_arr = {}


EV = [ElectricVehicle() for i in range(params.num_of_evs)]

for ev_id in range(params.num_of_evs):
    # create different random seed for each ev
    np.random.seed(ev_id)

    # create departure arrival times for one week
    dep_arr_time = dc.create_one_week_dep_arr_time(weekday_df=work_ev, weekend_df_list=casual_ev_df_list)

    # create at home status profile and save as ev object attribute
    EV[ev_id].at_home_status = dc.create_at_home_pattern(dep_arr_time=dep_arr_time, ev_id=ev_id)

    # create t_arr times and save as ev object attribute
    EV[ev_id].t_arr = dc.create_t_arr(dep_arr_time=dep_arr_time)

# save EV class in a pickle file
file_name = 'ev_data.pkl'
file_path = os.path.join(ev_model_path, file_name)

with open(file_path, 'wb') as f:
    pickle.dump(EV, f)

# with open('ev_data.pkl', 'rb') as f:
#     ev_data = pickle.load(f)
#
# print(len(ev_data))