from src.models.optimisation_models import build_model
from src.models import configs
from src.utils import solve_model
from src.utils.model_results import ModelResults
from src.config import independent_variables
from src.models.simulations import uncoordinated_charging_config_1


def execute_models(version, configurations, charging_strategies):
    for config in configurations:
        for charging_strategy in charging_strategies:
            # Set mip gap and time limit
            mip_gap = None
            time_limit = None
            verbose = False

            if charging_strategy == 'opportunistic' and config != 'config_1':
                verbose = True
                mip_gap = 0.5
                time_limit = 60 * 15
            elif charging_strategy == 'flexible' and config != 'config_1':
                verbose = True
                mip_gap = 0.9
                time_limit = 60 * 45

            # Run, solve, and save solved model
            run_and_save_solved_model(
                config,
                charging_strategy,
                version=version,
                mip_gap=mip_gap,
                time_limit=time_limit,
                verbose=verbose
            )


def run_and_save_solved_model(config: str,
                              charging_strategy: str,
                              version: str,
                              verbose=False,
                              time_limit=None,
                              mip_gap=None):
    config_map = {
        'config_1': configs.CPConfig.CONFIG_1,
        'config_2': configs.CPConfig.CONFIG_2,
        'config_3': configs.CPConfig.CONFIG_3,
    }

    strategy_map = {
        'uncoordinated': configs.ChargingStrategy.UNCOORDINATED,
        'opportunistic': configs.ChargingStrategy.OPPORTUNISTIC,
        'flexible': configs.ChargingStrategy.FLEXIBLE
    }

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

    if charging_strategy == 'uncoordinated':
        model = uncoordinated_charging_config_1.run_simulation_model(
            config_map[config],
            strategy_map[charging_strategy],
            independent_variables.p_cp_rated_uncoordinated_strategy
        )
        results = ModelResults(model, config_map[config], strategy_map[charging_strategy])

    else:
        model = build_model.BuildModel(
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy]
        )
        opt_model = model.get_optimisation_model()

        # Solve model_data
        solved_model, calc_mip_gap = solve_model.solve_optimisation_model(
            opt_model,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap
        )

        # Save results
        results = ModelResults(solved_model, config_map[config], strategy_map[charging_strategy], calc_mip_gap)

    results.save_model_to_pickle(version=version)

    return results


