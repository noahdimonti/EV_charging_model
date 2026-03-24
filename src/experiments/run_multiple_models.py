import pandas as pd
from src.pipelines.multiple_models_pipeline import run_multiple_models
from src.experiments.obj_weights_map import obj_weights_dict


def main():
    pd.options.display.max_columns = None

    # Mapping for mip_gap, time_limit, and verbose for each model
    solver_settings = {  # { model_name: [mip_gap (%), time_limit (minute), verbose] }
        'config_1_uncoordinated': [None, None, False, 4],
        'config_1_opportunistic': [1, 120, True, 16],
        'config_1_flexible': [1, 240, True, 16],

        'config_2_uncoordinated': [None, None, False, 4],
        'config_2_opportunistic': [3, 360, True, 32],
        'config_2_flexible': [3, 360, True, 32],

        'config_3_uncoordinated': [None, None, False, 4],
        'config_3_opportunistic': [5, 360, True, 32],
        'config_3_flexible': [5, 720, True, 32],
    }

    version = 'balanced'

    obj_weights = obj_weights_dict[version]

    configurations = [
        'config_1',
        'config_2',
        'config_3',
    ]

    # charging_strategies = ['uncoordinated']

    charging_strategies = [
        'opportunistic',
        'flexible',
    ]

    run_multiple_models(
        configurations=configurations,
        charging_strategies=charging_strategies,
        version=version,
        obj_weights=obj_weights,
        solver_settings=solver_settings,
    )



if __name__ == '__main__':
    main()
