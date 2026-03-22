


obj_weights_dict = {
        f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max': {
            f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max': {'economic': 1, 'technical': 1, 'social': 1}
        },

        f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max_cap{ev_capacity_range_low}-{ev_capacity_range_high}': {
            f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max_cap{ev_capacity_range_low}-{ev_capacity_range_high}': {
                'economic': 1, 'technical': 1, 'social': 1}
        },

        f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max_cap{ev_capacity_range_low}-{ev_capacity_range_high}'
        f'_{avg_travel_distance}km': {
            f'norm_w_sum_{min_initial_soc}min_{max_initial_soc}max_cap{ev_capacity_range_low}-{ev_capacity_range_high}'
            f'_{avg_travel_distance}km': {
                'economic': 1, 'technical': 1, 'social': 1}
        },
}