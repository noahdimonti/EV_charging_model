from contextlib import contextmanager
from pathlib import Path
import os
import sys

from pyomo.contrib.pynumero.examples.callback.reactor_design import model

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import params
from src.config.ev_params import load_ev_data
from src.experiments.obj_weights_map import obj_weights_dict
from src.experiments.solver_settings import solver_settings as sol
from src.models.optimisation_models.run_optimisation import run_optimisation_model


PARAMS_COMBINATION = [
    {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 25},
    {'min_soc': 0.2, 'max_soc': 0.4, 'cap': '35_60', 'avg_dist': 25},
    {'min_soc': 0.6, 'max_soc': 0.8, 'cap': '35_60', 'avg_dist': 25},
    {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '30_40', 'avg_dist': 25},
    {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '55_65', 'avg_dist': 25},
    {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 15},
    {'min_soc': 0.4, 'max_soc': 0.6, 'cap': '35_60', 'avg_dist': 35},
]


def parse_capacity_range(capacity_range: str) -> tuple[int, int]:
    low, high = capacity_range.split('_')
    return int(low), int(high)


def build_version_name(params_combination: dict[str, int | float | str]) -> str:
    return (
        f'balanced_sens_analysis_'
        f'avgdist{params_combination["avg_dist"]}km_'
        f'min{params_combination["min_soc"]}_max{params_combination["max_soc"]}_'
        f'cap{params_combination["cap"]}'
    )


def build_results_filepath(config: str, strategy: str, version: str) -> str:
    filename = (
        f'{config}_{strategy}_{params.num_of_evs}EVs_'
        f'{params.num_of_days}days_{version}.pkl'
    )
    return os.path.join(params.model_results_folder_path, filename)


@contextmanager
def temporary_ev_input_params(
        min_soc: float,
        max_soc: float,
        cap: str,
        avg_dist: int,
):
    original_values = {
        'min_initial_soc': params.min_initial_soc,
        'max_initial_soc': params.max_initial_soc,
        'ev_capacity_range_low': params.ev_capacity_range_low,
        'ev_capacity_range_high': params.ev_capacity_range_high,
        'avg_travel_distance': params.avg_travel_distance,
    }

    cap_low, cap_high = parse_capacity_range(cap)

    params.min_initial_soc = min_soc
    params.max_initial_soc = max_soc
    params.ev_capacity_range_low = cap_low
    params.ev_capacity_range_high = cap_high
    params.avg_travel_distance = avg_dist

    try:
        yield
    finally:
        params.min_initial_soc = original_values['min_initial_soc']
        params.max_initial_soc = original_values['max_initial_soc']
        params.ev_capacity_range_low = original_values['ev_capacity_range_low']
        params.ev_capacity_range_high = original_values['ev_capacity_range_high']
        params.avg_travel_distance = original_values['avg_travel_distance']


def main():
    config = 'config_2'
    charging_strategy = 'opportunistic'
    obj_weights = obj_weights_dict['balanced']
    overwrite_existing = False

    model_name = f'{config}_{charging_strategy}'

    solver_settings = {
        'mip_gap': sol[model_name][0],
        'time_limit': sol[model_name][1],
        'verbose': sol[model_name][2],
        'thread_count': sol[model_name][3],
    }

    for params_combination in PARAMS_COMBINATION:
        version = build_version_name(params_combination)
        result_filepath = build_results_filepath(config, charging_strategy, version)

        print('\n-----------------------------------------------------------')
        print(f'Running sensitivity analysis for version: {version}')
        print(f'Parameters: {params_combination}')
        print('-----------------------------------------------------------')

        if os.path.exists(result_filepath) and not overwrite_existing:
            print(f'Skipping existing result: {result_filepath}')
            continue

        with temporary_ev_input_params(
                min_soc=params_combination['min_soc'],
                max_soc=params_combination['max_soc'],
                cap=params_combination['cap'],
                avg_dist=params_combination['avg_dist'],
        ):
            ev_data = load_ev_data()
            print(f'Loaded EV input data: {ev_data.filename}')

            run_optimisation_model(
                config=config,
                charging_strategy=charging_strategy,
                version=version,
                obj_weights=obj_weights,
                ev_data=ev_data,
                verbose=solver_settings['verbose'],
                time_limit=solver_settings['time_limit'],
                mip_gap=solver_settings['mip_gap'],
                thread_count=solver_settings['thread_count'],
                save_model=True,
            )


if __name__ == '__main__':
    main()
