import os
import pyomo.environ as pyo
import pandas as pd
from src.models.optimisation_models.build_model import BuildModel
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from src.pipelines.experiments_pipeline.analyse_results import analyse_results
from src.models.utils.mapping import config_map, strategy_map
from src.config import params
from src.visualisation.epsilon_constraint.epsilon_sweep_plot import plot_epsilon


def main():
    # Set parameters
    config = 'config_1'
    charging_strategy = 'opportunistic'

    eps_bounds = {
        'economic_objective': {'max': 17259.90204917811, 'min': 2553.7367866118643},
        'technical_objective': {'max': 1338.0490559198788, 'min': 163.3830737085036},
        'social_objective': {'max': 1971.9830234911428, 'min': 494.3083107545863},
    }

    # Epsilon sweep ranges
    epsilon_ranges = {
        # 'economic': [17259.90, 17000, 14000, 11000, 8000, 5000, 2553.74],
        # 'economic': [0.9, 0.7, 0.5, 0.3, 0.1],
        # 'economic': [0.95, 0.75, 0.55, 0.35, 0.15],
        'economic': [i for i in range(17000, 2500, -1500)],

        # 'technical': [1338.05, 1000, 800, 600, 400, 200, 163.38],
        # 'technical': [0.9, 0.7, 0.5, 0.3, 0.1],
        # 'technical': [0.75, 0.6, 0.45, 0.3, 0.15],
        'technical': [i for i in range(1400, 150, -150)],

        # 'social': [1971.98, 1800, 1500, 1200, 900, 600, 494.31],
        # 'social': [0.9, 0.7, 0.5, 0.3, 0.1],
        # 'social': [0.9, 0.8, 0.7, 0.6, 0.5, 0.4],
        'social': [i for i in range(1900, 450, -150)],

    }

    # Build model constraints
    model_builder = BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy],
        version='epsilon_test',
    )
    model = model_builder.get_optimisation_model()

    # Pipeline controls
    run = False
    plot = True

    if run:
        run_epsilon_sweep_single_primary(
            config=config,
            charging_strategy=charging_strategy,
            model=model,
            epsilon_ranges=epsilon_ranges,
        )

    if plot:

        plot_epsilon(config, charging_strategy)


def run_epsilon_sweep_single_primary(
        config: str,
        charging_strategy: str,
        model: pyo.ConcreteModel,
        epsilon_ranges: dict[str, list[int | float]]):

    objectives = [
        'social',
        'technical',
        'economic',
    ]


    # Initialise results list
    epsilon_sweep_results = []

    sweep_count = 0
    infeasible_epsilon = []

    for primary in objectives:
        # Get secondary objective names
        secondary = [o for o in objectives if o != primary]

        for eps1 in epsilon_ranges[secondary[0]]:
            for eps2 in epsilon_ranges[secondary[1]]:
                sweep_count += 1
                print(f'\n------ Sweep count: {sweep_count} ------')
                print(f'Primary objective: {primary.capitalize()}')
                print(f'{secondary[0].capitalize()} epsilon: {eps1}')
                print(f'{secondary[1].capitalize()} epsilon: {eps2}')

                # Set the objective function to primary objective
                model.obj_function.set_value(
                    expr=getattr(model, f'{primary}_objective')
                )

                # Set epsilon bounds for the secondary objectives
                getattr(model, f'{secondary[0]}_epsilon_constraint').set_value(
                    expr=getattr(model, f'{secondary[0]}_objective') <= eps1
                )
                getattr(model, f'{secondary[1]}_epsilon_constraint').set_value(
                    expr=getattr(model, f'{secondary[1]}_objective') <= eps2
                )

                # Set model version
                version = f'epsilon_test_{primary}_{secondary[0]}{eps1}_{secondary[1]}{eps2}'

                # Run optimisation model
                try:
                    model_results = run_optimisation_model(
                        config=config,
                        charging_strategy=charging_strategy,
                        version=version,
                        model=model,
                        verbose=True,
                        time_limit=5,
                        mip_gap=1
                    )

                    epsilon_sweep_results.append(model_results.objective_components)

                except Exception or AttributeError as e:
                    print(e)
                    infeasible_epsilon.append({
                        'primary': primary,
                        f'{secondary[0]}': eps1,
                        f'{secondary[1]}': eps2
                    })
                    continue

                raw, formatted = analyse_results(
                    [config],
                    [charging_strategy],
                    version,
                    save_df=False,
                )
                print(formatted)

        #         break
        #     break
        # break

    # Convert into a dataframe
    print(epsilon_sweep_results)
    eps_sweep_df = pd.DataFrame(epsilon_sweep_results)
    inf_epsilon_df = pd.DataFrame(infeasible_epsilon)
    print(eps_sweep_df)

    # Save dataframe
    eps_filepath = os.path.join(params.data_output_path, 'epsilon_constraint')
    eps_sweep_df.to_csv(f'{eps_filepath}/epsilon_sweep_{config}_{charging_strategy}.csv')
    inf_epsilon_df.to_csv(f'{eps_filepath}/infeasible_epsilon_{config}_{charging_strategy}.csv')

    pd.set_option('display.max_rows', None)
    print('\nSolution values')
    print(eps_sweep_df)

    print('\nInfeasible epsilon')
    print(inf_epsilon_df)


if __name__ == '__main__':
    main()
