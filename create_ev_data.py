import pandas as pd
import numpy as np
import data_cleaning as dc
import pickle
import os
from ElectricVehicle import ElectricVehicle
from pprint import pprint
import params

# initialise data
timestamps = params.timestamps
periods_in_a_day = params.periods_in_a_day
num_of_days = params.num_of_days
min_SOC = params.min_SOC
max_SOC = params.max_SOC
final_SOC = params.final_SOC
travel_dist_std_dev = params.travel_dist_std_dev
energy_consumption_per_km = params.energy_consumption_per_km
P_EV_max = params.P_EV_max

# files and folders path
vista_raw_path = '/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling Data/Potential Datasets/vista/T_VISTA1218_V1.csv'
work_ev_path = ('/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling '
                'Data/Potential Datasets/vista/VISTA_Time_HomeDeAr_WorkVehicle.csv')
casual_ev_path = ('/Users/noahdimonti/Documents/Uni/MPhil in Eng and CS/EV Apartment Building Project/Modelling '
                  'Data/Potential Datasets/vista/VISTA_Time_HomeDeAr_CasualVehicle.csv')
ev_model_path = '/Users/noahdimonti/Developer/PycharmProjects/EV_model_test/'
pickle_filename = 'ev_data.pkl'


# data initialisation and cleaning functions
def initialise_and_clean_work_ev():
    work_ev = pd.read_csv(work_ev_path)
    work_ev = dc.clean_raw_data(work_ev)
    work_ev = dc.convert_to_timestamp(df=work_ev, date_time=params.start_date_time)
    work_ev = dc.remove_outliers(work_ev)

    return work_ev


# initialise and clean casual_ev data (for weekends)
# clean data
def initialise_and_clean_casual_ev():
    casual_ev = pd.read_csv(casual_ev_path)
    casual_ev.rename(columns={'Three _2nd_ARRTIME': 'Three_2nd_ARRTIME',
                              'Three _2nd_DEPTIME': 'Three_2nd_DEPTIME'}, inplace=True)
    casual_ev = dc.clean_raw_data(casual_ev)
    casual_ev = dc.convert_to_timestamp(df=casual_ev, date_time=params.start_date_time)

    # Split into dataframes for once, twice, and thrice casual EVs
    casual_ev_df_list = [
        casual_ev[['Once_DEPTIME', 'Once_ARRTIME']],
        casual_ev[['Twice_1st_DEPTIME', 'Twice_1st_ARRTIME', 'Twice_2nd_DEPTIME', 'Twice_2nd_ARRTIME']],
        casual_ev[['Three_1st_DEPTIME', 'Three_1st_ARRTIME', 'Three_2nd_DEPTIME', 'Three_2nd_ARRTIME',
                   'Three_3rd_DEPTIME', 'Three_3rd_ARRTIME']]
    ]

    return [dc.remove_outliers(df) for df in casual_ev_df_list]


# EV creation function
def create_ev_instances(num_of_evs, num_of_days, work_ev, casual_ev_list):
    ev_list = [
        ElectricVehicle(
            timestamps=timestamps,
            periods_in_a_day=periods_in_a_day,
            num_of_days=num_of_days,
            min_soc=min_SOC,
            max_soc=max_SOC,
            p_ev_max=P_EV_max
        ) for _ in range(num_of_evs)
    ]

    for ev_id in range(num_of_evs):
        # create different random seed for each ev
        np.random.seed(ev_id)

        if params.num_of_days == 7:
            # create departure arrival times for one week
            dep_arr_time = dc.create_one_week_dep_arr_time(weekday_df=work_ev, weekend_df_list=casual_ev_list)
        else:
            # create departure arrival times for however many days
            dep_arr_time = dc.create_dep_arr_time(df=work_ev, num_of_days=num_of_days)

        # create at home status profile and save as ev object attribute
        ev_list[ev_id].at_home_status = dc.create_at_home_pattern(dep_arr_time=dep_arr_time, ev_id=ev_id)

        # create t_arr times and save as ev object attribute
        ev_list[ev_id].t_arr = dc.create_t_arr(dep_arr_time=dep_arr_time)

        # create t_dep times and save as ev object attribute
        ev_list[ev_id].t_dep = dc.create_t_dep(dep_arr_time=dep_arr_time)

    return ev_list


# save function
# def save_ev_data(ev_list, path=ev_model_path, filename=pickle_filename):
#     file_path = os.path.join(path, filename)
#     with open(file_path, 'wb') as f:
#         pickle.dump(ev_list, f)


def initialise_ev_data(ev_data: list, num_of_evs: int, avg_travel_distance: float):
    # open data
    # with open('ev_data.pkl', 'rb') as f:
    #     ev_data = pickle.load(f)
    # pprint(ev_data)

    # instantiate EV objects in a list
    ev_list = [
        ElectricVehicle(
            timestamps=timestamps,
            periods_in_a_day=periods_in_a_day,
            num_of_days=num_of_days,
            min_soc=min_SOC,
            max_soc=max_SOC,
            p_ev_max=P_EV_max
        ) for _ in range(num_of_evs)
    ]

    np.random.seed(0)
    max_capacity_of_EVs = np.random.choice([i for i in range(35, 60)], size=num_of_evs)
    random_SOC_init = np.random.uniform(low=min_SOC, high=max_SOC, size=num_of_evs)

    ev_at_home_status_profile_list = []
    ev_charging_power_list = []

    # take data from pickle file and put them in EV class attributes
    for ev_id in range(num_of_evs):
        # initialise ev parameters
        ev_list[ev_id].at_home_status = ev_data[ev_id].at_home_status
        ev_list[ev_id].t_arr = ev_data[ev_id].t_arr
        ev_list[ev_id].t_dep = ev_data[ev_id].t_dep
        ev_list[ev_id].travel_energy = ev_data[ev_id].travel_energy

        ev_list[ev_id].capacity_of_ev = max_capacity_of_EVs[ev_id]
        ev_list[ev_id].soc_init = random_SOC_init[ev_id] * ev_list[ev_id].capacity_of_ev
        ev_list[ev_id].soc_max = max_SOC * ev_list[ev_id].capacity_of_ev
        ev_list[ev_id].soc_min = min_SOC * ev_list[ev_id].capacity_of_ev
        ev_list[ev_id].soc_final = final_SOC * ev_list[ev_id].capacity_of_ev

        # create a list of ev at home status dataframes
        ev_at_home_status_profile_list.append(ev_list[ev_id].at_home_status)

        # create a list of ev charging power dataframes
        ev_charging_power_list.append(ev_list[ev_id].charging_power)

        np.random.seed(ev_id)
        # set travel_energy_consumption
        if len(ev_list[ev_id].t_dep) == len(ev_list[ev_id].t_arr):
            for time in ev_list[ev_id].t_arr:
                rand_distance = np.random.normal(loc=avg_travel_distance, scale=travel_dist_std_dev, size=1)
                rand_travel_consumption = energy_consumption_per_km * rand_distance  # in kWh

                ev_list[ev_id].travel_energy.append(rand_travel_consumption)

                ev_list[ev_id].travel_energy_t_arr[time] = rand_travel_consumption

    return ev_list


# main function
def main(num_of_evs, avg_travel_distance):
    # initialise and clean data
    work_ev = initialise_and_clean_work_ev()
    casual_ev_list = initialise_and_clean_casual_ev()

    # create ev instances
    ev_data = create_ev_instances(num_of_evs, num_of_days, work_ev, casual_ev_list)

    # initialise ev_list
    ev_list = initialise_ev_data(ev_data, num_of_evs, avg_travel_distance)

    return ev_list

    # save to file
    # save_ev_data(ev_list)