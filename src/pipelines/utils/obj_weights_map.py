
obj_weights_dict = {
        'min_econ': {'economic': 1, 'technical': 0, 'social': 0},
        'min_tech': {'economic': 0, 'technical': 1, 'social': 0},
        'min_soc': {'economic': 0, 'technical': 0, 'social': 1},

        'econ_tech': {'economic': 0.5, 'technical': 0.5, 'social': 0},
        'econ_soc': {'economic': 0.5, 'technical': 0, 'social': 0.5},
        'tech_soc': {'economic': 0, 'technical': 0.5, 'social': 0.5},

        'balanced': {'economic': 1, 'technical': 1, 'social': 1}
}