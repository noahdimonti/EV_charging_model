import pandas as pd
from src.pipelines.run_models.pipeline import multiple_models_pipeline
from src.pipelines.utils.argparser import get_parser


def main(argv=None):
    pd.options.display.max_columns = None
    parser = get_parser()

    parser.add_argument('-w', '--obj_weights_type', type=str,
                        help="Objective weights type (e.g. extremes, balanced, dominant, pairwise)")

    args = parser.parse_args(argv)

    configurations = [
        # args.config
        'config_1',
        'config_2',
        # 'config_3',
    ]
    charging_strategies = [
        # args.charging_strategy
        'uncoordinated',
        'opportunistic',
        # 'flexible',
    ]

    # Objective weights
    obj_weights_dict = {
        'extremes': {
            'min_econ': {'economic': 1, 'technical': 0, 'social': 0},
            'min_tech': {'economic': 0, 'technical': 1, 'social': 0},
            'min_soc': {'economic': 0, 'technical': 0, 'social': 1},
        },

        'norm_w_sum': {
            'norm_w_sum': {'economic': 1, 'technical': 1, 'social': 1}
        },

        'pairwise': {
            'econ_tech_pair': {'economic': 0.5, 'technical': 0.5, 'social': 0},
            'econ_soc_pair': {'economic': 0.5, 'technical': 0, 'social': 0.5},
            'tech_soc_pair': {'economic': 0, 'technical': 0.5, 'social': 0.5},
        },

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

    args.obj_weights_type = 'norm_w_sum'

    # Execute model, analyse, and plot
    for obj, weights in obj_weights_dict[f'{args.obj_weights_type}'].items():
        version = obj
        obj_weights = weights
        run_model = True
        analyse = True
        plot = False

        multiple_models_pipeline(
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
        [
            # '-c', 'config_1',
            # '-s', 'opportunistic',
            # # '-w', f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max'
            # '-w', f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max'
            #       f'_cap{ev_capacity_range_low}-{ev_capacity_range_high}_{avg_travel_distance}km'

        ]
    )
