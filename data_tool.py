import pandas as pd


class EVData:
    def __init__(self):
        self.t_arr = []
        self.timeseries = None


def create_timeseries_at_home_pattern_once(df, dep_col: str, arr_col: str, time_resolution=15, num_of_ev=10,
                                           start_date_time='2019-01-01 00:00:00', rand_state=0):
    sample = df.sample(num_of_ev, random_state=rand_state)

    ev_data = []
    for sample_row in sample.iterrows():
        timeseries = pd.DataFrame(pd.date_range(start=start_date_time, periods=(60 / time_resolution) * 24,
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
