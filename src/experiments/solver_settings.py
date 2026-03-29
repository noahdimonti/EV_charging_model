

# Mapping for mip_gap, time_limit, and verbose for each model
solver_settings = {  # { model_name: [mip_gap (%), time_limit (minute), verbose, num threads] }
    'config_1_uncoordinated': [None, None, False, 8],
    'config_1_opportunistic': [1, 120, True, 16],
    'config_1_flexible': [1, 240, True, 16],

    'config_2_uncoordinated': [None, None, False, 8],
    'config_2_opportunistic': [3, 360, True, 32],
    'config_2_flexible': [3, 360, True, 32],

    'config_3_uncoordinated': [None, None, False, 8],
    'config_3_opportunistic': [5, 360, True, 32],
    'config_3_flexible': [5, 720, True, 32],
}