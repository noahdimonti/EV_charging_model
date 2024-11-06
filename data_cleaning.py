import pandas as pd


def clean_raw_data(df, col_names: list):

    df.dropna(axis=0, how='any', inplace=True)

    for col in col_names:
        df = df[df[f'{col}'] // 60 < 24]

    return df


def convert_to_timestamp(df, col_names: list):
    new_df = pd.DataFrame()

    for col_name in col_names:
        hour = (df[f'{col_name}'] // 60).astype(int)
        minute = (df[f'{col_name}'] % 60).astype(int)

        new_df[col_name] = (pd.Timestamp(2019, 1, 1) +
                            pd.to_timedelta(hour, unit='h') +
                            pd.to_timedelta(minute, unit='m'))
        new_df[f'{col_name}'].astype('datetime64[ns]')

        new_df[f'{col_name}'] = new_df[f'{col_name}'].dt.floor('15min')

    return new_df


def remove_outliers_once(df, dep: str, arr: str):
    # this function removes data where departure time is after arrival time
    df = df[df[f'{dep}'] < df[f'{arr}']]

    return df

'''
cols = list(casual_ev_three.columns)
list_of_conditions = []
for index, value in enumerate(cols):
    try:
        list_of_conditions.append(f'casual_ev_three[\'{cols[index]}\'] < casual_ev_three[\'{cols[index + 1]}\']')
    except IndexError:
        break

a = ''
for index, condition in enumerate(list_of_conditions):
    if index < len(list_of_conditions)-1:
        a = f'{a}({condition}) & '
    else:
        a = f'{a}({condition})'
'''


def remove_outliers_twice(df):
    condition_twice = ((df['Twice_1st_DEPTIME'] < df['Twice_1st_ARRTIME']) &
                       (df['Twice_1st_ARRTIME'] < df['Twice_2nd_DEPTIME']) &
                       (df['Twice_2nd_DEPTIME'] < df['Twice_2nd_ARRTIME']))

    df = df[condition_twice]

    return df


def remove_outliers_three(df):
    condition_three = ((df['Three_1st_DEPTIME'] < df['Three_1st_ARRTIME']) &
                       (df['Three_1st_ARRTIME'] < df['Three_2nd_DEPTIME']) &
                       (df['Three_2nd_DEPTIME'] < df['Three_2nd_ARRTIME']) &
                       (df['Three_2nd_ARRTIME'] < df['Three_3rd_DEPTIME']) &
                       (df['Three_3rd_DEPTIME'] < df['Three_3rd_ARRTIME']))

    df = df[condition_three]

    return df

class EVData:
    def __init__(self):
        self.t_arr = []
        self.timeseries = None


def create_timeseries_at_home_pattern_once(df, dep_col: str, arr_col: str, time_resolution=15, num_of_ev=10,
                                           start_date_time='2019-01-01 00:00:00', rand_state=0):

    sample = df.sample(num_of_ev, random_state=rand_state)

    ev_data = []
    for sample_row in sample.iterrows():
        timeseries = pd.DataFrame(pd.date_range(start=start_date_time, periods=(60/time_resolution)*24,
                                                freq=f'{time_resolution}min'),

              columns=['timestamp'])
        home_status = []
        data = EVData()

        for timeseries_row in timeseries.iterrows():
            if timeseries_row[1].timestamp < sample_row[1][f'{dep_col}']:
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1][f'{dep_col}']) &
                  (timeseries_row[1].timestamp < sample_row[1][f'{arr_col}'])):
                home_status.append(0)
            elif timeseries_row[1].timestamp >= sample_row[1][f'{arr_col}']:
                home_status.append(1)

        data.t_arr.append(str(sample_row[1][f'{arr_col}']))

        timeseries[f'EV_ID{sample_row[0]}'] = home_status
        data.timeseries = timeseries

        ev_data.append(data)

    return ev_data, sample


def create_timeseries_at_home_pattern_twice(df, arr_cols: list, time_resolution=15, num_of_ev=10,
                                           start_date_time='2019-01-01 00:00:00', rand_state=0):

    timeseries = pd.DataFrame(pd.date_range(start=start_date_time, periods=(60/time_resolution)*24,
                                            freq=f'{time_resolution}min'),
                              columns=['timestamp'])
    sample = df.sample(num_of_ev, random_state=rand_state)

    for sample_row in sample.iterrows():
        home_status = []

        for timeseries_row in timeseries.iterrows():
            if timeseries_row[1].timestamp < sample_row[1]['Twice_1st_DEPTIME']:
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Twice_1st_DEPTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Twice_1st_ARRTIME'])):
                home_status.append(0)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Twice_1st_ARRTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Twice_2nd_DEPTIME'])):
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Twice_2nd_DEPTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Twice_2nd_ARRTIME'])):
                home_status.append(0)
            elif timeseries_row[1].timestamp >= sample_row[1]['Twice_2nd_ARRTIME']:
                home_status.append(1)

        timeseries[f'EV_ID{sample_row[0]}'] = home_status

    ev_data = EVData()
    for col in arr_cols:
        ev_data.t_arr.extend(sample[col].astype(str))

    ev_data.timeseries = timeseries

    return timeseries


def create_timeseries_at_home_pattern_three(df, time_resolution=15, num_of_ev=10,
                                            start_date_time='2019-01-01 00:00:00', rand_state=0):

    timeseries = pd.DataFrame(pd.date_range(start=start_date_time, periods=(60/time_resolution)*24,
                                            freq=f'{time_resolution}min'),
                              columns=['timestamp'])
    sample = df.sample(num_of_ev, random_state=rand_state)

    for sample_row in sample.iterrows():
        home_status = []

        for timeseries_row in timeseries.iterrows():
            if timeseries_row[1].timestamp < sample_row[1]['Three_1st_DEPTIME']:
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Three_1st_DEPTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Three_1st_ARRTIME'])):
                home_status.append(0)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Three_1st_ARRTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Three_2nd_DEPTIME'])):
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Three_2nd_DEPTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Three_2nd_ARRTIME'])):
                home_status.append(0)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Three_2nd_ARRTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Three_3rd_DEPTIME'])):
                home_status.append(1)
            elif ((timeseries_row[1].timestamp >= sample_row[1]['Three_3rd_DEPTIME']) &
                  (timeseries_row[1].timestamp < sample_row[1]['Three_3rd_ARRTIME'])):
                home_status.append(0)
            elif timeseries_row[1].timestamp >= sample_row[1]['Three_3rd_ARRTIME']:
                home_status.append(1)

        timeseries[f'EV_ID{sample_row[0]}'] = home_status

    return timeseries