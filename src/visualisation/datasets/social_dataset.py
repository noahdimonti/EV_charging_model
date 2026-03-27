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

    # print(f'\n--- Model: {config} {strategy} ---')

    for ev_id in model_results.sets['EV_ID']:
        for t_arr in ev_data.t_arr_dict[ev_id]:
            wait_time = None

            for future_t in model_results.sets['TIME']:
                if future_t >= t_arr and model_results.variables['p_ev'][ev_id, future_t] > 0:
                    delta = future_t - t_arr
                    wait_time = round(delta.total_seconds() / 3600, 2)
                    # if wait_time > 50:
                    #     print(f'\nWait time over 50 hrs: {wait_time}')
                    #     print(f'EV ID: {ev_id}')
                    #     print(f'Arrival time: {t_arr}')
                    #     print(f'Arrival SOC: {model_results.variables['soc_ev'][ev_id, t_arr]}')
                    #     print(f'Charging time: {future_t}')
                    #     print(f'SOC pre charging: {model_results.variables['soc_ev'][ev_id, future_t]}')
                    # elif wait_time > 24 and wait_time < 50:
                    #     print(f'\nWait time over 24 hrs: {wait_time}')
                    #     print(f'EV ID: {ev_id}')
                    #     print(f'Arrival time: {t_arr}')
                    #     print(f'Arrival SOC: {model_results.variables['soc_ev'][ev_id, t_arr]}')
                    #     print(f'Charging time: {future_t}')
                    #     print(f'SOC pre charging: {model_results.variables['soc_ev'][ev_id, future_t]}')

                    break

            rows.append({
                'config': config_label,
                'strategy': strategy_label,
                'model': f'{config_label} - {strategy_label} Charging',
                'version': version,
                'wait_time': wait_time,
            })

    return rows


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

