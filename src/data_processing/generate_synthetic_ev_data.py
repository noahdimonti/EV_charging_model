import numpy as np
import pickle
import os
from scipy.stats import truncnorm

from src.config.params import max_initial_soc
from src.data_processing.electric_vehicle import ElectricVehicle
from src.config import params
import vista_data_cleaning as vdc
import generate_ev_dep_arr_data as gda


def main(num_of_evs, min_init_soc, max_init_soc, output_filename):
    # Initialise ready to use data_processing
    weekday_df, weekend_list = vdc.main()

    # create ev instances
    ev_instances = create_ev_instances(
        timestamps=params.timestamps,
        num_of_evs=num_of_evs,
        min_init_soc=min_init_soc,
        max_init_soc=max_init_soc,
        num_of_days=params.num_of_days,
        avg_travel_distance=params.avg_travel_distance,
        weekday_df=weekday_df,
        weekend_df_list=weekend_list
    )

    # Save data_processing into a pickle file
    folder_path = 'data/inputs/processed'
    file_path = os.path.join(params.project_root, folder_path)
    filename = os.path.join(file_path, output_filename)
    with open(filename, "wb") as f:
        pickle.dump(ev_instances, f)

    print(f'EV instances saved to {filename}.')

    return ev_instances


def create_ev_instances(timestamps, num_of_evs: int, min_init_soc: float, max_init_soc: float, num_of_days: int, avg_travel_distance: float, weekday_df, weekend_df_list):
    """Create EV instances and assign availability profiles."""

    # Initialise EV objects
    ev_instances_list = [ElectricVehicle(ev_id, timestamps) for ev_id in range(num_of_evs)]

    # Initialise EV attributes data_processing and assign to EV instances
    for ev_id, ev in enumerate(ev_instances_list):
        # Get EV dep arr times, capacity, and soc init
        dep_arr_times, capacity_of_EVs, SOC_init_of_EVs = generate_ev_attributes(
            num_of_evs,
            min_init_soc,
            max_init_soc,
            num_of_days,
            weekday_df,
            weekend_df_list
        )

        # Get travel energy consumption
        num_trips = int(len(dep_arr_times[ev_id]) / 2)
        travel_energy = generate_travel_energy_consumption(
            avg_travel_distance=avg_travel_distance,
            rand_seed=ev_id,
            number_of_trips=num_trips
        )

        # Assign EV attributes to EV instances
        ev.at_home_status = gda.create_at_home_pattern(dep_arr_time=dep_arr_times[ev_id], ev_id=ev_id)
        ev.t_arr = gda.create_t_arr(dep_arr_times[ev_id])
        ev.t_dep = gda.create_t_dep(dep_arr_times[ev_id])
        ev.travel_energy = travel_energy

        ev.battery_capacity = capacity_of_EVs[ev_id]
        ev.soc_init = SOC_init_of_EVs[ev_id] * capacity_of_EVs[ev_id]
        ev.soc_max = params.SOC_max * capacity_of_EVs[ev_id]
        ev.soc_critical = params.SOC_critical * capacity_of_EVs[ev_id]

    return ev_instances_list


def generate_ev_attributes(num_of_evs, min_init_soc, max_init_soc, num_of_days, weekday_df, weekend_df_list):
    """Generate EV attributes: departure arrival times, capacity, and SOC initial."""

    # Get departure and arrival times
    dep_arr_times = []
    for ev_id in range(num_of_evs):
        dep_arr = gda.get_dep_arr_time(num_of_days, weekday_df, weekend_df_list, ev_id)
        dep_arr_times.append(dep_arr)

    # Random seed
    rng = np.random.default_rng(0)
    # Generate EV capacities
    capacity_of_EVs = rng.choice(
        np.arange(params.ev_capacity_range_low, params.ev_capacity_range_high + 1),
        size=num_of_evs
    )

    # Generate initial SOC values
    SOC_init_of_EVs = rng.uniform(low=min_init_soc, high=max_init_soc, size=num_of_evs)

    return dep_arr_times, capacity_of_EVs, SOC_init_of_EVs


def generate_travel_energy_consumption(avg_travel_distance: float, rand_seed: int, number_of_trips: int):
    # Define the range, mean, and standard deviation
    lower, upper = 0, np.inf
    mean, std_dev = avg_travel_distance, params.travel_dist_std_dev

    # Calculate the parameters for truncnorm
    a, b = (lower - mean) / std_dev, (upper - mean) / std_dev

    # Generate truncated normal data_processing to avoid negative values
    rng = np.random.default_rng(rand_seed)
    travel_distances = truncnorm.rvs(a, b, loc=mean, scale=std_dev, size=number_of_trips, random_state=rng)

    # convert travel distance to consumed energy
    travel_energy_consumptions = (params.energy_consumption_per_km * travel_distances).tolist()  # in kWh

    return travel_energy_consumptions


if __name__ == '__main__':
    num_evs = None
    # num_evs = 100
    version = 'avgdist25km'
    min_init_soc = 0.6
    max_init_soc = 0.8

    if num_evs is not None:
        main(num_of_evs=num_evs,
             min_init_soc=min_init_soc,
             max_init_soc=max_init_soc,
             output_filename=f'EV_instances_{num_evs}_{version}_min{min_init_soc}_max{max_init_soc}'
             )
    else:
        raise ValueError('Provide a number of EV instances.')