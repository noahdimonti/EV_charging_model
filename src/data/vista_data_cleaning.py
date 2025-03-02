import pandas as pd
import numpy as np
from src.config import params


def main(start_date_time=params.start_date_time, min_at_home_time=params.min_time_at_home):
    # Files and folders path
    vista_raw_path = '../../data/raw/T_VISTA1218_V1.csv'
    work_ev_path = '../../data/raw/VISTA_Time_HomeDeAr_WorkVehicle.csv'
    casual_ev_path = '../../data/raw/VISTA_Time_HomeDeAr_CasualVehicle.csv'

    # create weekday and weekend dep-arr dataframes
    weekday = initialise_and_clean_work_ev(
        work_ev_path, start_date_time=start_date_time, min_at_home_time=min_at_home_time
    )
    weekend_list = initialise_and_clean_casual_ev(
        casual_ev_path, start_date_time=start_date_time, min_at_home_time=min_at_home_time
    )

    return weekday, weekend_list


def clean_raw_data(df):
    """
    Initial cleaning of raw vista data
    """
    df.dropna(axis=0, how='any', inplace=True)

    # remove values that is greater than 24 (only 24 hours in a day)
    for col in df.columns:
        df = df[df[f'{col}'] // 60 < 24]

    return df


def convert_to_timestamp(df, start_date_time, time_res=15):
    """
    Converting decimal timestamps to datetime timestamps
    """
    new_df = pd.DataFrame()

    for col_name in df.columns:
        # calculate hours and minutes from the values
        hour = (df[f'{col_name}'] // 60).astype(int)
        minute = (df[f'{col_name}'] % 60).astype(int)

        # convert hours and minutes into timestamp
        new_df[col_name] = (pd.Timestamp(start_date_time) +
                            pd.to_timedelta(hour, unit='h') +
                            pd.to_timedelta(minute, unit='m'))
        new_df[f'{col_name}'].astype('datetime64[ns]')

        new_df[f'{col_name}'] = new_df[f'{col_name}'].dt.floor(f'{time_res}min')

    return new_df


def remove_outliers(df, min_at_home_time):
    """
    Ensuring that departure and arrival time pairs are within reasonable constraints
    """
    # Initialise mask as True (all rows valid initially)
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

            # Ensure the time difference between dep2 and arr1 is at least min_at_home_time
            mask &= (df[dep_col] - df[prev_arr_col]) >= pd.Timedelta(minutes=min_at_home_time)

    # Filter the rows based on the mask
    df_cleaned = df[mask]

    return df_cleaned


def initialise_and_clean_work_ev(work_ev_path, start_date_time, min_at_home_time):
    """
    Clean EV data for weekdays (departure and arrival time pairs, once in a day).
    Returns a dataframe of departure and arrival columns.
    """
    work_ev = pd.read_csv(work_ev_path)
    work_ev = clean_raw_data(work_ev)
    work_ev = convert_to_timestamp(df=work_ev, start_date_time=start_date_time)
    work_ev = remove_outliers(work_ev, min_at_home_time)

    return work_ev


def initialise_and_clean_casual_ev(casual_ev_path, start_date_time, min_at_home_time):
    """
    Clean EV data for weekends (departure and arrival time pairs, more than once in a day).
    Returns a list of dataframes, columns are pairs of departure and arrival times for once in a day,
    twice in a day, and three times in a day.
    """
    casual_ev = pd.read_csv(casual_ev_path)
    casual_ev.rename(columns={'Three _2nd_ARRTIME': 'Three_2nd_ARRTIME',
                              'Three _2nd_DEPTIME': 'Three_2nd_DEPTIME'}, inplace=True)
    casual_ev = clean_raw_data(casual_ev)
    casual_ev = convert_to_timestamp(df=casual_ev, start_date_time=start_date_time)

    # Split into dataframes for once, twice, and thrice casual EVs
    casual_ev_df_list = [
        casual_ev[['Once_DEPTIME', 'Once_ARRTIME']],
        casual_ev[['Twice_1st_DEPTIME', 'Twice_1st_ARRTIME', 'Twice_2nd_DEPTIME', 'Twice_2nd_ARRTIME']],
        casual_ev[['Three_1st_DEPTIME', 'Three_1st_ARRTIME', 'Three_2nd_DEPTIME', 'Three_2nd_ARRTIME',
                   'Three_3rd_DEPTIME', 'Three_3rd_ARRTIME']]
    ]

    casual_ev_list = [remove_outliers(df, min_at_home_time) for df in casual_ev_df_list]

    return casual_ev_list


if __name__ == '__main__':
    main()