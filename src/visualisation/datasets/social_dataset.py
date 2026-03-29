import pandas as pd

from src.models.results.model_results import EvaluationMetrics, resolve_ev_data
from src.visualisation import io
from src.visualisation.labels import format_config_label, format_strategy_label


def build_soc_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)
            ev_data = resolve_ev_data(model_results)

            config_label = format_config_label(config)
            strategy_label = format_strategy_label(strategy)

            for ev_id in model_results.sets['EV_ID']:
                for time in model_results.sets['TIME']:
                    if time in ev_data.t_dep_dict[ev_id]:
                        soc_t_dep = (
                            model_results.variables['soc_ev'][ev_id, time]
                            / ev_data.soc_max_dict[ev_id]
                        ) * 100

                        rows.append({
                            'config': config_label,
                            'strategy': strategy_label,
                            'model': f'{config_label} - {strategy_label} Charging',
                            'ev_id': ev_id,
                            'time': time,
                            'soc_t_dep': soc_t_dep,
                        })

    df = pd.DataFrame(rows)
    df['config_num'] = df['config'].str.extract(r'(\d+)').astype(int)

    return df


def _build_wait_time_rows(
        config: str,
        strategy: str,
        version: str,
) -> list[dict]:
    model_results = io.load_model_results(config, strategy, version)
    ev_data = resolve_ev_data(model_results)
    rows = []

    config_label = format_config_label(config)
    strategy_label = format_strategy_label(strategy)

    for ev_id in model_results.sets['EV_ID']:
        for t_arr in ev_data.t_arr_dict[ev_id]:
            wait_time = None

            for future_t in model_results.sets['TIME']:
                if future_t >= t_arr and model_results.variables['p_ev'][ev_id, future_t] > 0:
                    delta = future_t - t_arr
                    wait_time = round(delta.total_seconds() / 3600, 2)
                    break

            rows.append({
                'config': config_label,
                'strategy': strategy_label,
                'model': f'{config_label} - {strategy_label} Charging',
                'version': version,
                'wait_time': wait_time,
            })

    return rows


def _get_pre_charge_soc_percent(
        model_results,
        ev_data,
        ev_id: int,
        arrival_time: pd.Timestamp,
        time_points: list[pd.Timestamp],
        time_position: dict[pd.Timestamp, int],
) -> float:
    """Return SOC at arrival before any charging at or after that arrival."""
    arrival_index = time_position[arrival_time]
    trip_index = ev_data.t_arr_dict[ev_id].index(arrival_time)

    if arrival_index == 0:
        pre_charge_soc = model_results.variables['soc_ev'][ev_id, arrival_time]
    else:
        previous_time = time_points[arrival_index - 1]
        previous_soc = model_results.variables['soc_ev'][ev_id, previous_time]
        pre_charge_soc = previous_soc - ev_data.travel_energy_dict[ev_id][trip_index]

    soc_percent = (pre_charge_soc / ev_data.soc_max_dict[ev_id]) * 100

    return max(0.0, min(100.0, soc_percent))


def build_wait_time_soc_scatter_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)
            ev_data = resolve_ev_data(model_results)

            config_label = format_config_label(config)
            strategy_label = format_strategy_label(strategy)
            time_points = sorted(model_results.sets['TIME'])
            time_position = {timestamp: idx for idx, timestamp in enumerate(time_points)}

            for ev_id in model_results.sets['EV_ID']:
                for arrival_time in ev_data.t_arr_dict[ev_id]:
                    wait_time = None
                    charge_start_time = None

                    for future_time in time_points:
                        if future_time >= arrival_time and model_results.variables['p_ev'][ev_id, future_time] > 0:
                            charge_start_time = future_time
                            delta = future_time - arrival_time
                            wait_time = round(delta.total_seconds() / 3600, 2)
                            break

                    if wait_time is None:
                        continue

                    rows.append({
                        'config': config_label,
                        'strategy': strategy_label,
                        'model': f'{config_label} - {strategy_label} Charging',
                        'version': version,
                        'ev_id': ev_id,
                        'arrival_time': arrival_time,
                        'charge_start_time': charge_start_time,
                        'wait_time': wait_time,
                        'soc_before_charging': _get_pre_charge_soc_percent(
                            model_results=model_results,
                            ev_data=ev_data,
                            ev_id=ev_id,
                            arrival_time=arrival_time,
                            time_points=time_points,
                            time_position=time_position,
                        ),
                    })

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=[
            'config',
            'strategy',
            'model',
            'version',
            'ev_id',
            'arrival_time',
            'charge_start_time',
            'wait_time',
            'soc_before_charging',
            'config_num',
        ])

    df['config_num'] = df['config'].str.extract(r'(\d+)').astype(int)

    return df



def build_wait_time_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            rows.extend(_build_wait_time_rows(config, strategy, version))

    df = pd.DataFrame(rows)
    df['config_num'] = df['config'].str.extract(r'(\d+)').astype(int)

    return df


def build_num_charging_days_df(
        configurations: list[str],
        charging_strategies: list[str],
        version: str,
) -> pd.DataFrame:
    rows = []

    for config in configurations:
        for strategy in charging_strategies:
            model_results = io.load_model_results(config, strategy, version)
            evaluation_metrics = EvaluationMetrics(model_results)

            rows.append({
                'config': format_config_label(config),
                'strategy': format_strategy_label(strategy),
                'model': f'{format_config_label(config)} - {format_strategy_label(strategy)} Charging',
                'num_charging_day': evaluation_metrics.metrics['avg_num_charging_days'],
            })

    df = pd.DataFrame(rows)
    df['config_num'] = df['config'].str.extract(r'(\d+)').astype(int)

    return df

