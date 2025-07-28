import pandas as pd
import matplotlib.pyplot as plt
import copy
from collections import deque, defaultdict
from src.config import params, ev_params
from src.models.simulations.config_2 import ChargingPointSlot
from src.data_processing.electric_vehicle import ElectricVehicle
from pprint import pprint


class UncoordinatedModelConfig3:
    def __init__(self,
                 ev_data: list,
                 household_load: pd.DataFrame,
                 p_cp_rated_scaled: float,
                 ev_to_cp_assignment: dict[int, list]  # keys: cp_id, values: list of ev_id
                 ):
        self.ev_data = ev_data
        self.household_load = household_load
        self.p_cp_rated_scaled = p_cp_rated_scaled
        self.ev_to_cp_assignment = ev_to_cp_assignment

        self.num_ev = params.num_of_evs
        self.cp_ids = list(self.ev_to_cp_assignment.keys())
        self.num_cp = len(self.cp_ids)
        self.charging_points = {cp: ChargingPointSlot(cp) for cp in self.cp_ids}
        self.is_cp_available = {cp: True for cp in self.cp_ids}
        self.idle: dict[int, list] = copy.deepcopy(self.ev_to_cp_assignment)
        self.is_charging: defaultdict[int, list[int]] = defaultdict(list)
        self.charging_queue: defaultdict[int, deque[int]] = defaultdict(deque)
        self.delta_t = pd.Timedelta(minutes=params.time_resolution)

    def simulate(self) -> list[ElectricVehicle]:
        for t in params.timestamps:
            if t == params.start_date_time:
                self._initialise_soc(t)

            else:
                for cp in self.cp_ids:
                    self._update_charging_queue(cp, t)
                    self._sort_charging_queue(cp, t)
                    self._connect_ev(cp, t)
                    self._handle_ev_disconnections(cp, t)
                    self._update_soc_and_power(cp, t)

            # self.print_debug(t)

        # self.quick_plot()

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

    def _update_charging_queue(self, cp_id, t):
        # Check if EVs in the idle list need to be added to the charging queue
        for ev in self.idle[cp_id][:]:
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Add EVs to charging queue
            if (self._is_at_home(ev, t)) and (prev_soc < soc_max) and (ev not in self.charging_queue[cp_id]):
                self.charging_queue[cp_id].append(ev)
                self.idle[cp_id].remove(ev)

        # Remove EV from charging queue if EV is away or has already reached soc_max
        for ev in self.charging_queue[cp_id].copy():
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Remove EV from charging queue
            if (t in self.ev_data[ev].t_dep) or (prev_soc == soc_max):
                self.charging_queue[cp_id].remove(ev)
                self.idle[cp_id].append(ev)

    def _sort_charging_queue(self, cp_id, t):
        self.charging_queue[cp_id] = deque(sorted(
            self.charging_queue[cp_id],
            key=lambda ev_id: (self._next_departure(ev_id, t), self._get_soc_priority(ev_id, t))
        ))

    def _connect_ev(self, cp_id, t):
        if (len(self.charging_queue[cp_id]) > 0) and (self.is_cp_available[cp_id]) and (t.time() not in params.no_charging_time):
            # Connect EV to CP and add it to is_charging list
            ev_queue_id = self.charging_queue[cp_id].popleft()
            self.charging_points[cp_id].connect_ev(ev_queue_id, t)
            self.is_charging[cp_id].append(ev_queue_id)
            self.is_cp_available[cp_id] = False

    def _handle_ev_disconnections(self, cp_id, t):
        for ev in self.is_charging[cp_id][:]:
            # Instantiate cp object
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
                self.is_charging[cp_id].remove(ev)
                self.idle[cp_id].append(ev)
                cp.disconnect_ev(t - self.delta_t)

                # Connect the next EV in the queue to CP
                if self.charging_queue[cp_id]:
                    next_ev_in_queue = self.charging_queue[cp_id].popleft()
                    cp.connect_ev(next_ev_in_queue, t)
                    self.is_charging[cp_id].append(next_ev_in_queue)

                else:
                    self.is_cp_available[cp_id] = True

    def _update_soc_and_power(self, cp_id, t):
        # Calculate maximum charging power per CP
        available_power_at_cp = (params.P_grid_max - self.household_load.loc[t].values.item()) / self.num_cp

        # Calculate p_ev and soc_ev for each EV
        for ev in self.ev_to_cp_assignment[cp_id]:
            # Define previous soc and soc_max
            prev_soc, soc_max = self._get_soc_and_max(ev, t)

            # Subtract travel energy if t is at arrival time
            if t in self.ev_data[ev].t_arr:
                k = ev_params.t_arr_dict[ev].index(t)
                prev_soc -= self.ev_data[ev].travel_energy[k]

            if ev in self.is_charging[cp_id]:
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

            elif ev not in self.is_charging[cp_id]:
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
        print(f'available cp: {self.is_cp_available}\n')

        for cp in self.charging_points.values():
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
            for cp in self.cp_ids:
                if ev in self.is_charging[cp]:
                    print(f'{params.GREEN}', end='')
                    _print_stats(ev)
                    print(f'{params.RESET}', end='')
                    break
                else:
                    continue

            if ev not in self.is_charging[cp]:
                _print_stats(ev)

            print('\n', end='')

        print('\n')

    def quick_plot(self):
        for ev in range(self.num_ev):
            plt.plot(self.ev_data[ev].soc)
            plt.show()





