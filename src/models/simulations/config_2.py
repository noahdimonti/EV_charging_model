import pandas as pd
import datetime
from collections import deque
from src.config import params, ev_params


class ChargingPointSlot:
    def __init__(self, cp_id: int):
        self.cp_id = cp_id

        self.ev_id = None
        self.charging_start_time = None
        self.charging_end_time = None
        self.charging_duration = None

    def connect_ev(self, ev_id, start_time):
        self.ev_id = ev_id
        self.charging_start_time = start_time
        self.charging_end_time = None

    def charge_ev(self, ev_id):
        pass

    def disconnect_ev(self, end_time):
        self.ev_id = None
        self.charging_end_time = end_time
        self.charging_duration = None


def uncoordinated_model_config_2(
        ev_data: list,
        household_load: pd.DataFrame,
        num_ev_at_home: pd.DataFrame,
        p_cp_rated_scaled: float,
        num_cp: int
):
    num_ev = params.num_of_evs

    # Create dataframe for merged EV at home status
    merged_ev_at_home_status = pd.concat([ev.at_home_status for ev in ev_data], axis=1)

    # Filter for the first departure after current time t
    def next_departure(ev_id, t):
        return min((dep_time for dep_time in ev_params.t_dep_dict[ev_id] if dep_time > t), default=max(params.timestamps))

    # Filter for EV SOC at time t
    def get_soc(ev_id, t):
        return ev_data[ev_id].soc.loc[t].values.item() / ev_data[ev_id].soc_max

    # Instantiate CP charging slots
    cp_slot_objs = [ChargingPointSlot(i) for i in range(num_cp)]
    num_available_cp = num_cp

    # Initiate a set of helper lists
    unordered_waiting_list = []
    is_charging = []
    idle = [i for i in range(num_ev)]
    charging_queue = deque()

    # Define CP maximum charging time settings
    idle_start_time = datetime.time(hour=params.idle_start_hour, minute=0)
    idle_end_time = datetime.time(hour=params.idle_end_hour, minute=0)

    max_charging_duration = pd.Timedelta(hours=params.max_charging_duration)

    for t in params.timestamps:
        print('----------------------------------')
        print(f'\nTIMESTAMP: {t}\n')
        print('----------------------------------')

        for ev in idle[:]:
            ev_at_home = merged_ev_at_home_status[f'EV_ID{ev}'].loc[t]
            soc = ev_data[ev].soc.loc[t].values.item()
            soc_max = ev_data[ev].soc_max

            if (ev_at_home == 1) and (soc < soc_max):  # AND soc < soc_max
                unordered_waiting_list.append(ev)
                idle.remove(ev)
                if len(charging_queue) > 0:
                    charging_queue.appendleft(ev)

        if len(charging_queue) == 0:
            charging_queue.extend(
                sorted(
                    unordered_waiting_list,
                    key=lambda ev_id: (next_departure(ev_id, t), get_soc(ev_id, t))
                )
            )

        if len(charging_queue) > 0:
            if num_available_cp > 0:  # if there is available CP
                for cp in cp_slot_objs:
                    if cp.ev_id is None:
                        try:
                            # Update lists
                            ev_queue_id = charging_queue.popleft()
                            cp.connect_ev(ev_queue_id, t)
                            num_available_cp -= 1
                            unordered_waiting_list.remove(ev_queue_id)
                            is_charging.append(ev_queue_id)
                        except IndexError:
                            continue

        # calculate maximum charging power per CP
        available_power_at_cp = (params.P_grid_max - household_load.loc[t].values.item()) / num_cp

        # Calculate p_ev and soc_ev for each EV
        for ev in range(num_ev):
            # Define helper variables
            soc_max = ev_data[ev].soc_max
            delta_t = pd.Timedelta(minutes=params.time_resolution)

            # Assign charging power and soc initial
            if t == params.start_date_time:
                ev_data[ev].charging_power.loc[t] = 0
                ev_data[ev].soc.loc[t] = ev_data[ev].soc_init
            else:
                prev_soc = ev_data[ev].soc.loc[t - delta_t].values.item()

                if ev in is_charging:
                    # EV is connected to CP: calculate charging power and soc
                    # Define available power and soc(t-1)
                    available_power = min(available_power_at_cp, p_cp_rated_scaled)

                    # Subtract travel energy if t is at arrival time
                    if t in ev_data[ev].t_arr:
                        k = ev_params.t_arr_dict[ev].index(t)
                        prev_soc -= ev_data[ev].travel_energy[k]

                    # Predict SOC based on available charging power
                    potential_soc = prev_soc + available_power

                    if potential_soc > soc_max:
                        # Calculate how much energy is needed to reach SOC max
                        remaining_to_charge = soc_max - prev_soc
                        p_ev = remaining_to_charge
                        soc_ev = soc_max
                    else:
                        # Assign available power to charging power and SOC accordingly
                        p_ev = available_power
                        soc_ev = potential_soc

                    # Conditions for when ev has to stop charging
                    prev_time = t - pd.Timedelta(minutes=params.time_resolution)
                    t_dep = next_departure(ev, prev_time)

                    # current_time = t.time()
                    # if idle_start_time <= current_time <= idle_end_time:
                    #     print(f'idle time: {current_time}')

                    # Get charging duration
                    for cp in cp_slot_objs:
                        if cp.ev_id == ev:
                            cp.charging_duration = t - cp.charging_start_time

                            if (t_dep == t) or (soc_ev == soc_max) or (
                                    cp.charging_duration >= max_charging_duration):
                                # Update lists:
                                is_charging.remove(ev)
                                idle.append(ev)
                                cp.disconnect_ev(prev_time)

                                # cp_slot_objs[cp_id].disconnect_ev(prev_time)
                                # Stop charging EV
                                ...

                                # Connect the next EV in the queue to the unoccupied CP
                                if len(charging_queue) > 0:
                                    next_ev_in_queue = charging_queue.popleft()
                                    cp.connect_ev(next_ev_in_queue, t)
                                    unordered_waiting_list.remove(next_ev_in_queue)
                                    is_charging.append(next_ev_in_queue)

                                    # Charge EV
                                    ...
                                else:
                                    num_available_cp += 1

                else:
                    # EV is NOT connected to CP: charging power is 0 and soc remains unchanged
                    p_ev = 0
                    soc_ev = prev_soc

                ev_data[ev].charging_power.loc[t] = p_ev
                ev_data[ev].soc.loc[t] = soc_ev





        print(f'\nunordered waiting list: {unordered_waiting_list}')
        print(f'charging queue: {charging_queue}')
        print(f'is charging: {is_charging}')
        print(f'idle: {idle}')
        print(f'available cp: {num_available_cp}\n')

        for cp in cp_slot_objs:
            print(cp.__dict__)

        print('\n')

        def print_stats():
            print(f'EV ID: {ev}')
            print(f'at home status: {ev_data[ev].at_home_status.loc[t].values.item()}')
            print(f'p ev: {ev_data[ev].charging_power.loc[t].values.item()}')
            print(f'soc: {ev_data[ev].soc.loc[t].values.item()}')
            print(f'soc max: {ev_data[ev].soc_max}')

        for ev in range(num_ev):
            if ev in is_charging:
                print(f'{params.GREEN}', end='')
                print_stats()
                print(f'{params.RESET}', end='')
            else:
                print_stats()
            print('\n', end='')


        print('\n')

        # break












