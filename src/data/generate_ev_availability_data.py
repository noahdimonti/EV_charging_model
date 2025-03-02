import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import vista_data_cleaning as vdc
from src.config import params
from pprint import pprint


"""
Convert cleaned vista data into EV availability profile (1: at home, 0: away).
Returns csv(?) with timestamps as index and EV_IDx as columns.
"""


def main(rand_seed, ev_id, num_of_weeks=params.num_of_weeks):
    weekday, weekend_list = vdc.main()

    dep_arr_times = create_multiple_weeks_dep_arr_time(
        num_of_weeks=num_of_weeks,
        weekday_df=weekday,
        weekend_df_list=weekend_list,
        rand_seed=rand_seed,
        ev_id=ev_id  # Pass EV ID for unique seeding
    )

    pprint(dep_arr_times)
    final = create_at_home_pattern(dep_arr_times, ev_id)

    return final


def create_dep_arr_time(df, num_of_days: int, rand_seed: int):
    """
    Create one pair of departure and arrival times each day, for the number of days provided.
    :param df: vista dataframe
    :param num_of_days: desired number of days
    :param rand_seed: random seed for sampling
    :return:
    """
    # take sample of dataframes according to how many number of days needed
    sample = df.sample(num_of_days, random_state=rand_seed)  # set random seed

    dep_arr_time = []
    # collect departure and arrival times by iterating through rows and columns of the dataframe
    for idx, row in enumerate(sample.itertuples()):
        for col in range(1, len(sample.columns)+1):
            timestamp = row[col] + pd.Timedelta(days=idx)
            dep_arr_time.append(timestamp)

    return dep_arr_time


def create_one_week_dep_arr_time(weekday_df, weekend_df_list: list, rand_seed: int):
    # create weekdays departure arrival times
    weekdays = create_dep_arr_time(df=weekday_df, num_of_days=5, rand_seed=rand_seed)

    # create weekends departure arrival times
    rng = np.random.default_rng(rand_seed)  # set random seed
    rand_travel_freq = rng.choice([0, 1, 2], p=list(params.travel_freq_probability.values()))
    weekends = []
    for i in range(2):
        new_time = create_dep_arr_time(df=weekend_df_list[rand_travel_freq], num_of_days=1, rand_seed=rand_seed)
        new_time = [timestamp + pd.Timedelta(days=5+i) for timestamp in new_time]
        weekends.append(new_time)

    # flatten the list
    weekends = sum(weekends, [])

    # merge weekdays and weekends
    one_week = weekdays + weekends

    return one_week


def create_multiple_weeks_dep_arr_time(num_of_weeks: int, weekday_df, weekend_df_list: list, rand_seed: int, ev_id):
    """
    Create multiple weeks of departure and arrival times.

    :param num_of_weeks: Number of weeks to generate.
    :param weekday_df: DataFrame containing weekday travel data.
    :param weekend_df_list: List of DataFrames for weekend travel data (different frequencies).
    :param rand_seed: Random seed for reproducibility.
    :return: List of departure and arrival timestamps for the given number of weeks.
    """
    all_weeks = []

    for week in range(num_of_weeks):
        # Offset random seed using EV ID and week number
        week_seed = rand_seed + (ev_id * 1000) + week
        print(f'Week: {week}, Random Seed: {week_seed}')  # Debugging output

        week_times = create_one_week_dep_arr_time(weekday_df, weekend_df_list,
                                                      rand_seed + week)  # Offset seed
        week_times = [timestamp + pd.Timedelta(days=7 * week) for timestamp in week_times]  # Shift by week
        all_weeks.extend(week_times)

    return all_weeks


def create_t_arr(dep_arr_time: list):
    # arrival times are the odd index of dep_arr_time list
    t_arr = dep_arr_time[1::2]

    return t_arr


def create_t_dep(dep_arr_time: list):
    # departure times are the even index of dep_arr_time list
    t_dep = dep_arr_time[0::2]

    return t_dep


def create_at_home_pattern(dep_arr_time: list, ev_id: int, time_res=15):
    # create timestamp based on dep_arr_time list
    start_date = min(dep_arr_time).normalize()
    num_of_days = max(dep_arr_time).day - min(dep_arr_time).day + 1
    date_range = pd.date_range(start=start_date, periods=int(num_of_days*(60/time_res)*24), freq=f'{time_res}min')

    df = pd.DataFrame(date_range, columns=['timestamp'])

    # initialise the pattern by assigning 1 to all values, assuming all EVs start at home
    df[f'EV_ID{ev_id}'] = 1

    # initialise the first switch to zero
    current_state = 0
    for ts in dep_arr_time:
        # toggle the state at the given timestamp
        df.loc[df['timestamp'] >= ts, f'EV_ID{ev_id}'] = current_state
        # toggle the state (1 -> 0 or 0 -> 1)
        current_state = 0 if current_state == 1 else 1

    # make timestamp the index
    df.set_index(keys='timestamp', inplace=True)

    return df


if __name__ == '__main__':
    main()