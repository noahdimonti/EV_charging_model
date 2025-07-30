import pyomo.environ as pyo
from src.models.optimisation_models.build_model import BuildModel
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.models.utils.mapping import config_map, strategy_map


# Set parameters
config = 'config_1'
charging_strategy = 'opportunistic'

objectives = ['economic', 'technical', 'social']

eps_bounds = {
    'economic_objective': {'max': 17259.90204917811, 'min': 2553.7367866118643},
    'social_objective': {'max': 1971.9830234911428, 'min': 494.3083107545863},
    'technical_objective': {'max': 1338.0490559198788, 'min': 163.3830737085036}
}

# Epsilon sweep ranges
epsilon_ranges = {
    'economic': [15000, 12000, 9000, 6000, 3000],
    'technical': [1000, 800, 600, 400, 200],
    'social': [1800, 1500, 1200, 900, 600]
}

# Build model constraints
model_builder = BuildModel(
    config=config_map[config],
    charging_strategy=strategy_map[charging_strategy],
    version='epsilon_test',
)
model = model_builder.get_optimisation_model()

# Initialise results list
epsilon_sweep_results = []

sweep_count = 0


for primary in objectives:
    print(f'\n--- Primary objective: {primary.capitalize()} ---')

    # Get secondary objective names
    secondary = [o for o in objectives if o != primary]

    for eps1 in epsilon_ranges[secondary[0]]:
        for eps2 in epsilon_ranges[secondary[1]]:
            sweep_count += 1
            print(f'\n--- Sweep count: {sweep_count} ---')

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

            # raw, formatted = analyse_results([config], [charging_strategy], version=version)
            #
            # print(formatted)

            # print(eps1, eps2)
            # print(model.obj_function.display())
            # print(model.economic_objective.expr)
            # print(model.technical_objective.display())
            # print(model.social_objective.display())

    break

print(epsilon_sweep_results)


