

def pareto_parallel_plot():
    # Parallel coordinates plot for the Pareto front
    conf_type, conf_num = args.config.split('_')

    fig = px.parallel_coordinates(
        pareto_front,
        dimensions=objective_cols,
        color='distance_to_ideal',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={
            **{col: f'{col.capitalize()} (↓)' for col in objective_cols},
            'distance_to_ideal': 'Distance to Ideal'
        },
        title=f'Pareto Front Parallel Coordinates - {conf_type.capitalize()} {conf_num} {args.charging_strategy.capitalize()}',
    )

    parallel_plot_filepath = os.path.join(params.data_output_path,
                                          f'augmecon/parallel_plot_{args.config}_{args.charging_strategy}_{args.grid_points}gp.png')

    fig.write_image(parallel_plot_filepath, scale=2)
    print(f'\nPlot saved to {parallel_plot_filepath}')

    # fig.show()
