import pickle
from src.config import params

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