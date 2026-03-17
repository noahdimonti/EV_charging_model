import pandas as pd
from src.pipelines.experiments_pipeline.pipeline import run_model_pipeline
from src.utils.argparser import get_parser

def main(argv=None):
    pd.options.display.max_columns = None
    parser = get_parser()

    parser.add_argument('-w', '--obj_weights_type', type=str,
                        help="Objective weights type (e.g. extremes, balanced, dominant, pairwise)")

    args = parser.parse_args(argv)

    configurations = [
        # 'config_1',
        # 'config_2',
        'config_3',
    ]
    charging_strategies = [
        # 'uncoordinated',
        # 'opportunistic',
        'flexible',
    ]

    # Objective weights
    obj_weights_dict = {
        'extremes': {  # DONE
            'min_econ': {'economic': 1, 'technical': 0, 'social': 0},
            'min_tech': {'economic': 0, 'technical': 1, 'social': 0},
            'min_soc': {'economic': 0, 'technical': 0, 'social': 1},
        },

        'norm_w_sum': {  # DONE
            'norm_w_sum': {'economic': 1, 'technical': 1, 'social': 1}
        },

        'balanced': {
            'balanced': {'economic': 0.333, 'technical': 0.333, 'social': 0.334},
        },

        'balanced_test': {
            'balanced_test': {'economic': 0.333, 'technical': 0.333, 'social': 0.334},
        },

        'selected_solution': {
            'selected_solution': {'economic': 0.35, 'technical': 0.15, 'social': 0.5}
        },

        'selected_solution_test': {
            'selected_solution_test': {'economic': 0.35, 'technical': 0.15, 'social': 0.5}
        },

        'pairwise': {
            'econ_tech_pair': {'economic': 0.5, 'technical': 0.5, 'social': 0},
            'econ_soc_pair': {'economic': 0.5, 'technical': 0, 'social': 0.5},
            'tech_soc_pair': {'economic': 0, 'technical': 0.5, 'social': 0.5},
        },

        'pairwise_test1': {
            'econ_tech_pair': {'economic': 1, 'technical': 1, 'social': 0},
            },

        'pairwise_test2': {
            'econ_soc_pair': {'economic': 1, 'technical': 0, 'social': 1},
        },

        'pairwise_test3': {
            'tech_soc_pair': {'economic': 0, 'technical': 1, 'social': 1},
        }


    }

    # Mapping for mip_gap, time_limit, and verbose for each model
    solver_settings = {  # { model_name: [mip_gap (%), time_limit (minute), verbose] }
        'config_1_uncoordinated': [None, None, False],
        'config_1_opportunistic': [1, 120, True],
        'config_1_flexible': [1, 240, True],

        'config_2_uncoordinated': [None, None, False],
        'config_2_opportunistic': [3, 360, True],
        'config_2_flexible': [3, 360, True],

        'config_3_uncoordinated': [None, None, False],
        'config_3_opportunistic': [5, 360, True],
        'config_3_flexible': [4, 360, True],
    }

    # Execute model, analyse, and plot
    for obj, weights in obj_weights_dict[f'{args.obj_weights_type}'].items():
        version = obj
        obj_weights = weights
        run_model = True
        analyse = True
        plot = False

        run_model_pipeline(
            configurations=configurations,
            charging_strategies=charging_strategies,
            version=version,
            run_model=run_model,
            analyse=analyse,
            plot=plot,
            solver_settings=solver_settings,
            obj_weights=obj_weights,
            thread_count=args.thread_count
        )


if __name__ == '__main__':
    main(
        # [
        #     '-c', 'config_1',
        #     '-s', 'uncoordinated',
        #     '-w', 'norm_w_sum'
        # ]
    )
