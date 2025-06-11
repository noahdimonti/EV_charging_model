
tariff_type = 'flat'

# The "best" objective weights so far based on pareto ranks
obj_weights = {
    'economic_weight': 0.7,
    'technical_weight': 0.2,
    'social_weight': 0.1
}

obj_weights_from_sensitivity_analysis = {
    'config_1_opportunistic': {
        'economic_weight': 0.7,
        'technical_weight': 0.2,
        'social_weight': 0.1
    },
    'config_1_flexible': {
        'economic_weight': 0.4,
        'technical_weight': 0.5,
        'social_weight': 0.1
    },
}