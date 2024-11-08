import pandas as pd
import numpy as np


def clean_raw_data(df):

    df.dropna(axis=0, how='any', inplace=True)

    # remove values that is greater than 24 (only 24 hours in a day)
    for col in df.columns:
        df = df[df[f'{col}'] // 60 < 24]

    return df


def convert_to_timestamp(df, date_time, time_res=15):
    new_df = pd.DataFrame()

    for col_name in df.columns:
        # calculate hours and minutes from the values
        hour = (df[f'{col_name}'] // 60).astype(int)
        minute = (df[f'{col_name}'] % 60).astype(int)

        # convert hours and minutes into timestamp
        new_df[col_name] = (pd.Timestamp(date_time) +
                            pd.to_timedelta(hour, unit='h') +
                            pd.to_timedelta(minute, unit='m'))
        new_df[f'{col_name}'].astype('datetime64[ns]')

        new_df[f'{col_name}'] = new_df[f'{col_name}'].dt.floor(f'{time_res}min')

    return new_df


def remove_outliers(df):
    # Initialize mask as True (all rows valid initially)
    mask = True

    # Iterate over columns in pairs (dep1, arr1), (dep2, arr2), etc.
    for i in range(0, len(df.columns)-1, 2):
        dep_col = df.columns[i]
        arr_col = df.columns[i + 1]

        # Check if departure is earlier than arrival for the current pair
        mask &= df[dep_col] < df[arr_col]

        # Check if the current departure is strictly later than the previous arrival
        if i > 0:  # Not for the first pair (there is no previous arrival)
            prev_arr_col = df.columns[i - 1]  # The previous arrival column (e.g., arr1 for dep2)
            mask &= df[dep_col] > df[prev_arr_col]  # dep2 > arr1, dep3 > arr2, etc.

    # Filter the rows based on the mask
    df_cleaned = df[mask]

    return df_cleaned


def create_dep_arr_time(df, num_of_days: int):
    # take sample of dataframes according to how many number of days needed
    sample = df.sample(num_of_days)

    dep_arr_time = []
    # collect departure and arrival times by iterating through rows and columns of the dataframe
    for idx, row in enumerate(sample.itertuples()):
        for col in range(1, len(sample.columns)+1):
            timestamp = row[col] + pd.Timedelta(days=idx)
            dep_arr_time.append(timestamp)

    return dep_arr_time


def create_one_week_dep_arr_time(weekday_df, weekend_df_list: list):
    rand_travel_freq = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2])

    # create weekdays departure arrival times
    weekdays = create_dep_arr_time(df=weekday_df, num_of_days=5)

    # create weekends departure arrival times
    weekends = []
    for i in range(2):
        new_time = create_dep_arr_time(df=weekend_df_list[rand_travel_freq], num_of_days=1)
        new_time = [timestamp + pd.Timedelta(days=5+i) for timestamp in new_time]
        weekends.append(new_time)

    # flatten the list
    weekends = sum(weekends, [])

    # merge weekdays and weekends
    one_week = weekdays + weekends

    return one_week


def create_t_arr(dep_arr_time: list):
    # arrival times are the odd index of dep_arr_time list
    t_arr = dep_arr_time[1::2]

    return t_arr


def create_at_home_pattern(dep_arr_time: list, ev_id: int, time_res=15):
    # create timestamp based on dep_arr_time list
    start_date = min(dep_arr_time).normalize()
    num_of_days = max(dep_arr_time).day - min(dep_arr_time).day + 1
    date_range = pd.date_range(start=start_date, periods=int(num_of_days*(60/time_res)*24), freq=f'{time_res}min')

    df = pd.DataFrame(date_range, columns=['timestamp'])

    # initialise the pattern by assigning 1 to all values
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
