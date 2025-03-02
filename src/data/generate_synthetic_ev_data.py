import numpy as np
from scipy.stats import truncnorm
from src.config.electric_vehicle import ElectricVehicle
from src.config import params
import vista_data_cleaning as vdc
import generate_ev_availability_data as gen
from pprint import pprint


def main(num_of_evs, avg_travel_distance, min_soc):
    # initialise and clean data
    work_ev = gen.initialise_and_clean_work_ev()
    casual_ev_list = gen.initialise_and_clean_casual_ev()

    # create ev instances
    ev_data = create_ev_instances(num_of_evs, min_soc, params.num_of_days, work_ev, casual_ev_list)

    # initialise ev_list
    ev_list = initialise_ev_data(ev_data, num_of_evs, avg_travel_distance, min_soc)

    return ev_list


# EV creation function
def create_ev_instances(num_of_evs: int, min_soc: float, num_of_days: int, work_ev, casual_ev_list):
    # instantiate EV objects in a list
    ev_data = [
        ElectricVehicle(
            timestamps=params.timestamps,
            periods_in_a_day=params.periods_in_a_day,
            num_of_days=num_of_days,
            min_soc=min_soc,
            max_soc=params.max_SOC,
        ) for _ in range(num_of_evs)
    ]

    for ev_id in range(num_of_evs):
        # create different random seed for each ev
        np.random.seed(ev_id)

        if num_of_days == 7:
            # create departure arrival times for one week
            dep_arr_time = gen.create_one_week_dep_arr_time(weekday_df=work_ev, weekend_df_list=casual_ev_list, rand_seed=ev_id)
        elif num_of_days <= 5:
            # create departure arrival times for weekdays
            dep_arr_time = gen.create_dep_arr_time(df=work_ev, num_of_days=num_of_days, rand_seed=ev_id)
        elif num_of_days > 7:
            dep_arr_time = gen.create_multiple_weeks_dep_arr_time()

        # create at home status profile and save as ev object attribute
        ev_data[ev_id].at_home_status = vdc.create_at_home_pattern(dep_arr_time=dep_arr_time, ev_id=ev_id)

        # create t_arr times and save as ev object attribute
        ev_data[ev_id].t_arr = vdc.create_t_arr(dep_arr_time=dep_arr_time)

        # create t_dep times and save as ev object attribute
        ev_data[ev_id].t_dep = vdc.create_t_dep(dep_arr_time=dep_arr_time)

    return ev_data


def initialise_ev_data(ev_data: list, num_of_evs: int, avg_travel_distance: float, min_soc: float):
    # set random generator value for maximum capacity and soc of evs
    seed = 0
    rng = np.random.default_rng(seed)
    max_capacity_of_EVs = rng.choice(
        [i for i in range(params.ev_capacity_range_low, params.ev_capacity_range_high)], size=num_of_evs
    )

    rng = np.random.default_rng(seed)
    random_SOC_init = rng.uniform(low=params.min_initial_soc, high=params.max_initial_soc, size=num_of_evs)

    # take data from pickle file and put them in EV class attributes
    for ev_id in range(num_of_evs):
        # initialise ev parameters
        ev_data[ev_id].capacity_of_ev = max_capacity_of_EVs[ev_id]
        ev_data[ev_id].soc_init = random_SOC_init[ev_id] * ev_data[ev_id].capacity_of_ev
        ev_data[ev_id].soc_max = params.max_SOC * ev_data[ev_id].capacity_of_ev
        ev_data[ev_id].soc_min = min_soc * ev_data[ev_id].capacity_of_ev
        ev_data[ev_id].soc_final = params.final_SOC_default * ev_data[ev_id].capacity_of_ev

        # set travel_energy_consumption
        if len(ev_data[ev_id].t_dep) == len(ev_data[ev_id].t_arr):
            for time in ev_data[ev_id].t_arr:
                # Define the range, mean, and standard deviation
                lower, upper = 0, np.inf
                mean, std_dev = avg_travel_distance, params.travel_dist_std_dev

                # Calculate the parameters for truncnorm
                a, b = (lower - mean) / std_dev, (upper - mean) / std_dev

                # set different random seed for each EV
                rng = np.random.default_rng(ev_id)

                # Generate truncated normal data to avoid negative values
                rand_distance = float(truncnorm.rvs(a, b, loc=mean, scale=std_dev, size=1, random_state=rng))
                print(rand_distance)

                # convert travel distance to consumed energy
                rand_travel_consumption = float(params.energy_consumption_per_km * rand_distance)  # in kWh

                # append travel energy to attributes
                ev_data[ev_id].travel_energy.append(rand_travel_consumption)
                ev_data[ev_id].travel_energy_t_arr[time] = rand_travel_consumption

    return ev_data


if __name__ == "__main__":
    evlst = main(2, 20, 50)
    pprint(evlst[0].__dict__)