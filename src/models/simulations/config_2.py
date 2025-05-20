import pandas as pd
import matplotlib.pyplot as plt
import datetime
from collections import deque
from src.config import params, ev_params
from pprint import pprint


class ChargingPointSlot:
    def __init__(self, cp_id: int):
        self.cp_id = cp_id
        self.ev_id = None
        self.charging_duration = None
        self.charging_start_time = None
        self.charging_end_time = None

    def connect_ev(self, ev_id, start_time):
        self.ev_id = ev_id
        self.charging_start_time = start_time
        self.charging_end_time = None

    def disconnect_ev(self, end_time):
        self.ev_id = None
        self.charging_end_time = end_time
        self.charging_duration = None


# Filter for the first departure after current time t
def next_departure(ev_id, t):
    return min((dep_time for dep_time in ev_params.t_dep_dict[ev_id] if dep_time > t), default=max(params.timestamps))

# Filter for EV SOC at time t
def get_soc(ev_data, ev_id, t):
    return ev_data[ev_id].soc.loc[t].values.item() / ev_data[ev_id].soc_max



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

    # Instantiate CP charging slots
    charging_points = [ChargingPointSlot(i) for i in range(num_cp)]
    num_available_cp = num_cp

    # Initiate a set of helper lists and dictionary
    is_charging = []
    idle = [i for i in range(num_ev)]
    charging_queue = deque()
    ev_to_cp = {}


    for t in params.timestamps:
        print('----------------------------------')
        print(f'\nTIMESTAMP: {t}\n')
        print('----------------------------------')


        if t == pd.Timestamp('2022-02-23 01:00:00'):
            break

        # Define t-1
        delta_t = pd.Timedelta(minutes=params.time_resolution)



        # Check if EVs in the idle list need to be added to the charging queue
        for ev in idle[:]:
            ev_at_home = merged_ev_at_home_status[f'EV_ID{ev}'].loc[t]
            if t == params.start_date_time:
                pass
            else:
                prev_soc = ev_data[ev].soc.loc[t - delta_t].values.item()
                soc_max = ev_data[ev].soc_max

                # Add EVs to charging queue
                if (ev_at_home == 1) and (prev_soc < soc_max) and (ev not in charging_queue):
                    charging_queue.append(ev)
                    idle.remove(ev)


        # Remove EV from charging queue if EV is away or has already reached soc_max
        for ev in charging_queue.copy():
            if t == params.start_date_time:
                pass
            else:
                prev_soc = ev_data[ev].soc.loc[t - delta_t].values.item()
                soc_max = ev_data[ev].soc_max
                if (t in ev_data[ev].t_dep) or (prev_soc == soc_max):
                    charging_queue.remove(ev)
                    idle.append(ev)


        # Sort charging queue based on priority
        charging_queue = deque(sorted(
            charging_queue,
            key=lambda ev_id: (next_departure(ev_id, t), get_soc(ev_data, ev_id, t))
        ))


        # Connect EVs in the charging queue to available CPs
        if (len(charging_queue) > 0) and (num_available_cp > 0) and (t.time() not in params.no_charging_range_time):
            for cp in charging_points:
                if cp.ev_id is None:
                    try:
                        # Connect EV to CP and add it to is_charging list
                        ev_queue_id = charging_queue.popleft()
                        cp.connect_ev(ev_queue_id, t)
                        ev_to_cp[ev_queue_id] = cp.cp_id
                        num_available_cp -= 1
                        is_charging.append(ev_queue_id)
                    except IndexError:
                        continue



        # Conditions for when ev-cp connection has to be switched to another ev
        for ev in is_charging[:]:
            # CP connection settings
            cp_id = ev_to_cp[ev]
            cp = charging_points[cp_id]

            # Conditions for when to stop charging
            cp.charging_duration = t - cp.charging_start_time

            # Get next departure time
            next_t_dep = next_departure(ev, (t - delta_t))

            # Define helper variables
            soc_max = ev_data[ev].soc_max
            prev_soc = ev_data[ev].soc.loc[t - delta_t].values.item()

            # Switch EV connections when EV has to stop charging
            if (next_t_dep == t) or (prev_soc == soc_max) or (cp.charging_duration >= params.max_charging_duration):
                # Disconnect EV
                is_charging.remove(ev)
                idle.append(ev)
                cp.disconnect_ev(t - delta_t)
                ev_to_cp.pop(ev)

                # Connect the next EV in the queue to the unoccupied CP
                if len(charging_queue) > 0:
                    next_ev_in_queue = charging_queue.popleft()
                    print(f'next ev: {next_ev_in_queue}')
                    cp.connect_ev(next_ev_in_queue, t)
                    ev_to_cp[next_ev_in_queue] = cp.cp_id
                    is_charging.append(next_ev_in_queue)

                else:
                    num_available_cp += 1



        # Calculate maximum charging power per CP
        available_power_at_cp = (params.P_grid_max - household_load.loc[t].values.item()) / num_cp

        # Assigning initial soc for all EVs
        if t == params.start_date_time:
            for ev in range(num_ev):
                ev_data[ev].charging_power.loc[t] = 0
                ev_data[ev].soc.loc[t] = ev_data[ev].soc_init

        # Calculate p_ev and soc_ev for each EV if not the first timestamp
        else:
            for ev in range(num_ev):
                # Define helper variables
                soc_max = ev_data[ev].soc_max
                prev_soc = ev_data[ev].soc.loc[t - delta_t].values.item()

                # Subtract travel energy if t is at arrival time
                if t in ev_data[ev].t_arr:
                    k = ev_params.t_arr_dict[ev].index(t)
                    prev_soc -= ev_data[ev].travel_energy[k]

                if ev in is_charging:
                    # Define available power and soc(t-1)
                    available_power = min(available_power_at_cp, p_cp_rated_scaled)

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

                    ev_data[ev].charging_power.loc[t] = p_ev
                    ev_data[ev].soc.loc[t] = soc_ev

                elif ev not in is_charging:
                    ev_data[ev].charging_power.loc[t] = 0
                    ev_data[ev].soc.loc[t] = prev_soc





        # Print debug info
        print(f'charging queue: {charging_queue}')
        print(f'is charging: {is_charging}')
        print(f'idle: {idle}')
        print(f'available cp: {num_available_cp}\n')

        for cp in charging_points:
            print(cp.__dict__)

        print('\n')

        def print_stats(ev):
            soc = ev_data[ev].soc.loc[t].values.item()
            soc_max = ev_data[ev].soc_max

            print(f'EV ID: {ev}')
            print(f'at home status: {ev_data[ev].at_home_status.loc[t].values.item()}')
            print(f'p ev: {ev_data[ev].charging_power.loc[t].values.item()}')
            print(f'soc: {soc}')
            print(f'soc max: {soc_max}')
            print(f'soc percentage: {(soc / soc_max * 100):.2f}%')

            print(f'dep times of ev {ev}:')
            # pprint(ev_params.t_dep_dict[ev])

        for ev in range(num_ev):
            if ev in is_charging:
                print(f'{params.GREEN}', end='')
                print_stats(ev)
                print(f'{params.RESET}', end='')
            else:
                print_stats(ev)
            print('\n', end='')


        print('\n')

    print(f'arrival time of EV 1: {ev_params.t_arr_dict[1]}')

    for ev in range(num_ev):
        plt.plot(ev_data[ev].soc)
        # plt.show()











