import pickle
import os
from collections import defaultdict
from dataclasses import dataclass
from copy import deepcopy
from src.config import params
from pprint import pprint


@dataclass
class EVData:
    filename: str
    ev_instance_list: list
    soc_init_dict: dict
    soc_critical_dict: dict
    soc_max_dict: dict
    at_home_status_dict: dict
    t_arr_dict: dict
    t_dep_dict: dict
    travel_energy_dict: dict
    t_dep_on_day: dict
    charging_efficiency: float



def load_ev_data() -> EVData:
    # Load EV data
    folder_path = (f'data/inputs/ev_data/EV_instances_100_avgdist{params.avg_travel_distance}km'
                   f'_min{params.min_initial_soc}_max{params.max_initial_soc}'
                   f'_cap{params.ev_capacity_range_low}_{params.ev_capacity_range_high}')

    filename = os.path.join(params.project_root, folder_path)
    with open(filename, 'rb') as f:
        ev_instance_list = pickle.load(f)

    # Slice data
    ev_instance_list = deepcopy(ev_instance_list[:params.num_of_evs]
)
    # Initialise data
    soc_init_dict = {ev.ev_id: ev.soc_init for ev in ev_instance_list}
    soc_critical_dict = {ev.ev_id: ev.soc_critical for ev in ev_instance_list}
    soc_max_dict = {ev.ev_id: ev.soc_max for ev in ev_instance_list}

    at_home_status_dict = {ev.ev_id: ev.at_home_status for ev in ev_instance_list}
    t_arr_dict = {ev.ev_id: ev.t_arr for ev in ev_instance_list}
    t_dep_dict = {ev.ev_id: ev.t_dep for ev in ev_instance_list}
    travel_energy_dict = {ev.ev_id: ev.travel_energy for ev in ev_instance_list}

    t_dep_on_day = defaultdict(list)  # {day: [(ev_id, t_dep), ...]}

    for ev_id, times in t_dep_dict.items():
        for t in times:
            t_dep_on_day[t.date()].append((ev_id, t))

    # EV charging efficiency
    charging_efficiency = 0.95  # (%)

    return EVData(
        filename=filename,
        ev_instance_list=ev_instance_list,
        soc_init_dict=soc_init_dict,
        soc_critical_dict=soc_critical_dict,
        soc_max_dict=soc_max_dict,
        at_home_status_dict=at_home_status_dict,
        t_arr_dict=t_arr_dict,
        t_dep_dict=t_dep_dict,
        travel_energy_dict=travel_energy_dict,
        t_dep_on_day=dict(t_dep_on_day),
        charging_efficiency=charging_efficiency,
    )
