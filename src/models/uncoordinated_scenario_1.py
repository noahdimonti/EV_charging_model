import pandas as pd
from src.data import generate_synthetic_ev_data
from src.config.uncoordinated_model import UncoordinatedModel


def simulate_uncoordinated_model(p_ev_max: float, tariff_type: str, num_of_evs: int, avg_travel_distance: float,
                                 min_soc: float):
    # instantiate EV objects
    ev_data = create_ev_data.main(num_of_evs, avg_travel_distance, min_soc)

    # create ev at home pattern profile
    all_ev_profiles = pd.concat([ev.at_home_status for ev in ev_data], axis=1)
    all_ev_profiles['n_ev_at_home'] = all_ev_profiles.sum(axis=1).astype(int)

    # create household load profile
    household_load = params.household_load

    # convert p_ev_max according to resolution
    p_ev_max_per_resolution = p_ev_max / params.P_EV_resolution_factor

    # uncoordinated charging scenario algorithm
    for id, ev in enumerate(ev_data):
        for t in all_ev_profiles.index:
            # check how much power left after being used for load
            if params.P_grid_max >= household_load.loc[t].values:
                ccp_capacity = params.P_grid_max - household_load.loc[t]
            else:
                grid_overload = ValueError('Demand is higher than the maximum grid capacity.')
                raise grid_overload

            # check maximum charging power based on how many evs are connected
            if all_ev_profiles['n_ev_at_home'].loc[t] > 0:
                max_cp_capacity = ccp_capacity / all_ev_profiles['n_ev_at_home'].loc[t]
            else:
                max_cp_capacity = ccp_capacity

            # check if ev is at home or not
            if all_ev_profiles[f'EV_ID{id}'].loc[t] == 0:
                ev.charging_power.loc[t] = 0
            else:
                # assign ev charging power when ev is at home
                if max_cp_capacity.values >= p_ev_max_per_resolution:
                    # if available charging power is higher than p_ev_max, charging power is assigned as p_ev_max
                    ev.charging_power.loc[t] = p_ev_max_per_resolution
                elif max_cp_capacity.values < p_ev_max_per_resolution:
                    # if available charging power is less, then assign whatever is available
                    ev.charging_power.loc[t] = max_cp_capacity.values

            # tracking the SOC
            time_delta = pd.Timedelta(minutes=params.time_resolution)

            if t == params.start_date_time:
                ev.soc.loc[t] = ev.soc_init
                ev.charging_power.loc[t] = 0

            elif (t != params.start_date_time) & (t not in ev.t_arr):
                ev.soc.loc[t] = (ev.soc.loc[t - time_delta] +
                                 ev.charging_power.loc[t].values)

                # make sure soc does not exceed the soc max limit
                if ev.soc.loc[t].values <= ev.soc_max:
                    pass
                else:
                    # calculate how much power needed to charge until soc reaches soc_max
                    remaining_to_charge = (ev.soc_max - ev.soc.loc[t - time_delta].values)

                    ev.soc.loc[t] = (ev.soc.loc[t - time_delta] + remaining_to_charge)

                    ev.charging_power.loc[t] = remaining_to_charge

            elif (t != params.start_date_time) & (t in ev.t_arr):
                ev.soc.loc[t] = ((ev.soc.loc[t - time_delta] + ev.charging_power.loc[t].values) -
                                 ev.travel_energy_t_arr[t])

    # instantiate model
    model = UncoordinatedModel(
        name=f'US1_{tariff_type.upper()}_{num_of_evs}EVs_{avg_travel_distance}km_SOCmin{int(min_soc * 100)}%'
    )

    # assign values to model attributes
    df = pd.concat([ev.charging_power for ev in ev_data], axis=1)
    df['ev_load'] = df.sum(axis=1)
    df['household_load'] = params.household_load
    df['grid'] = df['ev_load'] + df['household_load']
    df['total_load'] = df['ev_load'] + df['household_load']

    model.ev_load = df['ev_load']
    model.household_load = df['household_load']
    model.grid = df['grid']
    model.total_load = df['total_load']
    model.at_home_status = all_ev_profiles['n_ev_at_home']

    model.p_ev_max = p_ev_max
    model.num_of_cps = num_of_evs

    return model


def check(p_ev_max: float, tariff_type: str, num_of_evs: int, avg_travel_distance: float,
          min_soc: float):
    # Instantiate EV objects
    ev_data = create_ev_data.main(num_of_evs, avg_travel_distance, min_soc)

    # Create EV at-home pattern profile
    all_ev_profiles = pd.concat([ev.at_home_status for ev in ev_data], axis=1)
    all_ev_profiles['n_ev_at_home'] = all_ev_profiles.sum(axis=1).astype(int)

    # Create household load profile
    household_load = params.household_load

    # Convert p_ev_max according to resolution
    p_ev_max_per_resolution = p_ev_max / params.P_EV_resolution_factor

    # Precompute grid capacity constraints to avoid repeated checks
    if (household_load > params.P_grid_max).any().any():
        raise ValueError("Demand is higher than the maximum grid capacity.")

    # Iterate over EVs
    for id, ev in enumerate(ev_data):
        ev_profile_col = f'EV_ID{id}'

        # Check if this EV column exists in the profile
        if ev_profile_col not in all_ev_profiles.columns:
            raise ValueError(f"Missing EV profile column: {ev_profile_col}")

        ev_profile = all_ev_profiles[ev_profile_col]  # Extract EV-specific profile
        charging_power = []  # Initialize charging power list for efficiency
        soc = []  # Initialize SOC list for efficiency

        for t, n_ev_at_home in zip(all_ev_profiles.index, all_ev_profiles['n_ev_at_home']):
            # Calculate CP capacity (remaining grid capacity)
            cp_capacity = params.P_grid_max - household_load.loc[t].values

            # Calculate maximum charging power per EV
            max_cp_capacity = cp_capacity / n_ev_at_home if n_ev_at_home > 0 else cp_capacity

            if t == params.start_date_time:
                # Initial SOC and charging power
                soc.append(ev.soc_init)
                charging_power.append(0)
            else:
                # If EV is not at home, charging power is 0
                if ev_profile.loc[t] == 0:
                    charging_power.append(0)
                    soc.append(soc[-1])  # SOC remains unchanged
                else:
                    # EV is at home: calculate charging power
                    available_power = min(max_cp_capacity, p_ev_max_per_resolution)

                    # Predict SOC based on charging power
                    potential_soc = soc[-1] + available_power

                    if potential_soc > ev.soc_max:
                        # Calculate how much energy is needed to reach SOC max
                        remaining_to_charge = ev.soc_max - soc[-1]  # Energy needed to reach max SOC
                        charging_power.append(remaining_to_charge)
                        soc.append(ev.soc_max)  # Cap SOC at the maximum
                    else:
                        charging_power.append(available_power)  # Use full available power for charging
                        soc.append(potential_soc)  # Update SOC normally

                    # Deduct travel energy if the EV is traveling
                    if t in ev.t_arr:
                        soc[-1] -= ev.travel_energy_t_arr[t]

        # Assign calculated lists to EV attributes
        ev.charging_power = pd.Series(charging_power, index=all_ev_profiles.index)
        ev.soc = pd.Series(soc, index=all_ev_profiles.index)

    # instantiate model
    model = UncoordinatedModel(
        name=f'US1_{tariff_type.upper()}_{num_of_evs}EVs_{avg_travel_distance}km_SOCmin{int(min_soc * 100)}%'
    )

    # assign values to model attributes
    df = pd.concat([ev.charging_power for ev in ev_data], axis=1)
    df['ev_load'] = df.sum(axis=1)
    df['household_load'] = params.household_load
    df['grid'] = df['ev_load'] + df['household_load']
    df['total_load'] = df['ev_load'] + df['household_load']

    model.ev_load = df['ev_load']
    model.household_load = df['household_load']
    model.grid = df['grid']
    model.total_load = df['total_load']
    model.at_home_status = all_ev_profiles['n_ev_at_home']

    model.p_ev_max = p_ev_max
    model.num_of_cps = num_of_evs

    return model


import timeit

p_max = 2.4
tariff = 'flat'
ev = 100
avg_dist = 35
min_soc = 0.5


def before():
    simulate_uncoordinated_model(p_max, tariff, ev, avg_dist, min_soc)

old_model = simulate_uncoordinated_model(p_max, tariff, ev, avg_dist, min_soc)


def after():
    check(p_max, tariff, ev, avg_dist, min_soc)

new_model = check(p_max, tariff, ev, avg_dist, min_soc)


runtime_before = timeit.timeit(before, number=1)
print(f'runtime before: {runtime_before}')

runtime_after = timeit.timeit(after, number=1)
print(f'runtime after: {runtime_after}')


print(old_model.ev_load)
print(new_model.ev_load)