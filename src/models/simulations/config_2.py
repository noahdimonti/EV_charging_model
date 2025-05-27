import pandas as pd
import matplotlib.pyplot as plt
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


class UncoordinatedModelConfig2:
    def __init__(self, ev_data: list, household_load: pd.DataFrame, p_cp_rated_scaled: float, num_cp: int):
        self.ev_data = ev_data
        self.household_load = household_load
        self.p_cp_rated_scaled = p_cp_rated_scaled
        self.num_cp = num_cp

        self.num_ev = params.num_of_evs
        self.charging_points = [ChargingPointSlot(i) for i in range(num_cp)]
        self.num_available_cp = num_cp
        self.is_charging = []
        self.idle = [i for i in range(self.num_ev)]
        self.charging_queue = deque()
        self.ev_to_cp = {}
        self.delta_t = pd.Timedelta(minutes=params.time_resolution)

    def run(self):
        for t in params.timestamps:
            if t == params.start_date_time:
                self._initialise_soc(t)
            else:
                self._update_charging_queue(t)
                self._sort_charging_queue(t)
                self._connect_evs_to_available_cps(t)
                self._handle_ev_disconnections(t)
                self._update_soc_and_power(t)
            self.print_debug(t)

        self.quick_plot()

        return self.ev_data

    def _initialise_soc(self, t):
        for ev in range(self.num_ev):
            self.ev_data[ev].charging_power.loc[t] = 0
            self.ev_data[ev].soc.loc[t] = self.ev_data[ev].soc_init

    @staticmethod
    def _next_departure(ev_id, t):
        return min((dep_time for dep_time in ev_params.t_dep_dict[ev_id] if dep_time > t),
                   default=max(params.timestamps))

    def _get_soc_priority(self, ev_id, t):
        return self.ev_data[ev_id].soc.loc[t].values.item() / self.ev_data[ev_id].soc_max

    def _get_soc_and_max(self, ev_id, t):
        prev_soc = self.ev_data[ev_id].soc.loc[t - self.delta_t].values.item()
        soc_max = self.ev_data[ev_id].soc_max

        return prev_soc, soc_max

    def _is_at_home(self, ev_id, t):
        # Create dataframe for merged EV at home status
        merged_ev_at_home_status = pd.concat([ev.at_home_status for ev in self.ev_data], axis=1)

        return merged_ev_at_home_status[f'EV_ID{ev_id}'].loc[t] == 1

    def _update_charging_queue(self, t):
        # Check if EVs in the idle list need to be added to the charging queue
        for ev in self.idle[:]:
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Add EVs to charging queue
            if (self._is_at_home(ev, t)) and (prev_soc < soc_max) and (ev not in self.charging_queue):
                self.charging_queue.append(ev)
                self.idle.remove(ev)

        # Remove EV from charging queue if EV is away or has already reached soc_max
        for ev in self.charging_queue.copy():
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Remove EV from charging queue
            if (t in self.ev_data[ev].t_dep) or (prev_soc == soc_max):
                self.charging_queue.remove(ev)
                self.idle.append(ev)

    def _sort_charging_queue(self, t):
        self.charging_queue = deque(sorted(
            self.charging_queue,
            key=lambda ev_id: (self._next_departure(ev_id, t), self._get_soc_priority(ev_id, t))
        ))

    def _connect_evs_to_available_cps(self, t):
        if (len(self.charging_queue) > 0) and (self.num_available_cp > 0) and (t.time() not in params.no_charging_range_time):
            for cp in self.charging_points:
                if (cp.ev_id is None) and self.charging_queue:
                    # Connect EV to CP and add it to is_charging list
                    ev_queue_id = self.charging_queue.popleft()
                    cp.connect_ev(ev_queue_id, t)
                    self.ev_to_cp[ev_queue_id] = cp.cp_id
                    self.is_charging.append(ev_queue_id)
                    self.num_available_cp -= 1

    def _handle_ev_disconnections(self, t):
        for ev in self.is_charging[:]:
            # CP connection settings
            cp_id = self.ev_to_cp[ev]
            cp = self.charging_points[cp_id]

            # Calculate charging duration at time t
            cp.charging_duration = t - cp.charging_start_time

            # Get next departure time
            next_t_dep = self._next_departure(ev, (t - self.delta_t))

            if next_t_dep == params.timestamps[-1]:
                next_t_dep = None

            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Switch EV connections when EV has to stop charging
            if (next_t_dep == t) or (prev_soc == soc_max) or (cp.charging_duration >= params.max_charging_duration):
                # Disconnect EV
                self.is_charging.remove(ev)
                self.idle.append(ev)
                cp.disconnect_ev(t - self.delta_t)
                self.ev_to_cp.pop(ev)

                # Connect the next EV in the queue to the unoccupied CP
                if self.charging_queue:
                    next_ev_in_queue = self.charging_queue.popleft()
                    cp.connect_ev(next_ev_in_queue, t)
                    self.is_charging.append(next_ev_in_queue)
                    self.ev_to_cp[next_ev_in_queue] = cp.cp_id

                else:
                    self.num_available_cp += 1

    def _update_soc_and_power(self, t):
        # Calculate maximum charging power per CP
        available_power_at_cp = (params.P_grid_max - self.household_load.loc[t].values.item()) / self.num_cp

        # Calculate p_ev and soc_ev for each EV
        for ev in range(self.num_ev):
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Subtract travel energy if t is at arrival time
            if t in self.ev_data[ev].t_arr:
                k = ev_params.t_arr_dict[ev].index(t)
                prev_soc -= self.ev_data[ev].travel_energy[k]

            if ev in self.is_charging:
                # Define available power and soc(t-1)
                available_power = min(available_power_at_cp, self.p_cp_rated_scaled)

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

                self.ev_data[ev].charging_power.loc[t] = p_ev
                self.ev_data[ev].soc.loc[t] = soc_ev

            elif ev not in self.is_charging:
                self.ev_data[ev].charging_power.loc[t] = 0
                self.ev_data[ev].soc.loc[t] = prev_soc

    def print_debug(self, t):
        # Print debug info
        print('----------------------------------')
        print(f'\nTIMESTAMP: {t}\n')
        print('----------------------------------')

        print(f'charging queue: {self.charging_queue}')
        print(f'is charging: {self.is_charging}')
        print(f'idle: {self.idle}')
        print(f'available cp: {self.num_available_cp}\n')

        for cp in self.charging_points:
            print(cp.__dict__)

        print('\n')

        def _print_stats(ev_id):
            soc = self.ev_data[ev_id].soc.loc[t].values.item()
            soc_max = self.ev_data[ev_id].soc_max

            print(f'EV ID: {ev_id}')
            print(f'at home status: {self.ev_data[ev_id].at_home_status.loc[t].values.item()}')
            print(f'p ev: {self.ev_data[ev_id].charging_power.loc[t].values.item()}')
            print(f'soc: {soc}')
            print(f'soc max: {soc_max}')
            print(f'soc percentage: {(soc / soc_max * 100):.2f}%')

        for ev in range(self.num_ev):
            if ev in self.is_charging:
                print(f'{params.GREEN}', end='')
                _print_stats(ev)
                print(f'{params.RESET}', end='')
            else:
                _print_stats(ev)
            print('\n', end='')

        print('\n')

    def quick_plot(self):
        for ev in range(self.num_ev):
            plt.plot(self.ev_data[ev].soc)
            plt.show()








