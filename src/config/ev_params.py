import pickle
from src.config import params
from pprint import pprint

# Load EV data
filename = f'../../data/processed/EV_instances_{params.num_of_evs}'
with open(filename, "rb") as f:
    ev_instance_list = pickle.load(f)

# Initialise data
soc_init_dict = {ev.ev_id: ev.soc_init for ev in ev_instance_list}
soc_critical_dict = {ev.ev_id: ev.soc_critical for ev in ev_instance_list}
soc_max_dict = {ev.ev_id: ev.soc_max for ev in ev_instance_list}

at_home_status_dict = {ev.ev_id: ev.at_home_status for ev in ev_instance_list}
t_arr_dict = {ev.ev_id: ev.t_arr for ev in ev_instance_list}
t_dep_dict = {ev.ev_id: ev.t_dep for ev in ev_instance_list}
travel_energy_dict = {ev.ev_id: ev.travel_energy for ev in ev_instance_list}

charging_efficiency = 0.95  # (%)

# Sanity check
# print_check = True
print_check = False

if print_check:
    i = params.num_of_evs - 1
    pprint(t_dep_dict[i])
    pprint(t_arr_dict[i])
    pprint(travel_energy_dict[i])
    pprint(soc_critical_dict)
    pprint(soc_init_dict)
    pprint(soc_max_dict)
    pprint(at_home_status_dict)

    # for idx, t in enumerate(t_dep_dict[i]):
    #     if t is not t_dep_dict[i][-1]:
    #         time_delta = t_dep_dict[i][idx+1] - t_arr_dict[i][idx]
    #         print(time_delta)