import pandas as pd
from src.config import params, ev_params


class UncoordinatedModelConfig1:
    def __init__(self, ev_data: list,
                 household_load: pd.DataFrame,
                 num_ev_at_home: pd.DataFrame,
                 p_cp_rated_scaled: float
                 ):
        self.ev_data = ev_data
        self.household_load = household_load
        self.num_ev_at_home = num_ev_at_home
        self.p_cp_rated_scaled = p_cp_rated_scaled

    def run(self):
        for i, ev in enumerate(self.ev_data):
            # Initialise charging power and soc empty list
            p_ev = []
            soc_ev = []

            for t in params.timestamps:
                if t == params.start_date_time:
                    # Assign initial charging power and soc
                    p_ev.append(0)
                    soc_ev.append(ev.soc_init)
                elif not self._is_at_home(ev, t):
                    # EV is NOT at home: charging power is 0 and soc remains unchanged
                    p_ev.append(0)
                    soc_ev.append(soc_ev[-1])
                else:
                    # EV is at home: calculate charging power and soc
                    available_power_at_cp = self._get_available_power_per_cp(t)
                    p, soc = self._compute_power_and_soc(i, ev, t, soc_ev[-1], available_power_at_cp)

                    p_ev.append(p)
                    soc_ev.append(soc)

            # Assign charging power and soc list to dataframes in EV object
            print(f'ev: {ev}')
            print(f'p ev: {p_ev}')
            print(f'soc ev: {soc_ev}')
            ev.charging_power['charging_power'] = p_ev
            ev.soc['soc'] = soc_ev

        return self.ev_data

    def _get_available_power_per_cp(self, t):
        # Calculate CCP max capacity
        ccp_capacity = params.P_grid_max - self.household_load.loc[t].values.item()

        # calculate maximum charging power per EV divided evenly
        evs_at_home = self.num_ev_at_home.loc[t].values.item()

        return (ccp_capacity / evs_at_home) if evs_at_home > 1 else ccp_capacity

    @staticmethod
    def _is_at_home(ev, t):
        return ev.at_home_status.loc[t].values == 1

    def _compute_power_and_soc(self, i, ev, t, prev_soc, available_power_at_cp):
        available_power = min(available_power_at_cp, self.p_cp_rated_scaled)

        # Subtract travel energy if t is at arrival time
        if t in ev.t_arr:
            k = ev_params.t_arr_dict[i].index(t)
            prev_soc -= ev.travel_energy[k]

        # Predict SOC based on available charging power
        potential_soc = prev_soc + available_power

        if potential_soc > ev.soc_max:
            # Calculate how much energy is needed to reach SOC max
            remaining_to_charge = ev.soc_max - prev_soc
            return remaining_to_charge, ev.soc_max
        else:
            # Assign available power to charging power and SOC accordingly
            return available_power, potential_soc

