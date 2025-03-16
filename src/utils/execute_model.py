from src.models.optimisation_models import build_model, configs
from src.utils import solve_model
from src.utils.model_results import ModelResults


def run_model(config: str,
              charging_strategy: str,
              verbose=False,
              time_limit=None,
              mip_gap=None):

    config_map = {
        'config_1': configs.CPConfig.CONFIG_1,
        'config_2': configs.CPConfig.CONFIG_2,
        'config_3': configs.CPConfig.CONFIG_3,
    }

    strategy_map = {
        'opportunistic': configs.ChargingStrategy.OPPORTUNISTIC,
        'flexible': configs.ChargingStrategy.FLEXIBLE
    }

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

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
    results.save_model_to_pickle()

    return results




