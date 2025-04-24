from src.models.optimisation_models import build_model, solve_model
from src.models.mapping import config_map, strategy_map
from src.utils.model_results import ModelResults
from src.config import independent_variables
from src.models.simulations import run_simulation
import pyomo.environ as pyo


def execute_model(config: str,
                  charging_strategy: str,
                  version: str,
                  obj_weights: dict[str, float],
                  verbose=False,
                  time_limit: float = None,
                  mip_gap: float = None):

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

    if charging_strategy == 'uncoordinated':
        model = run_simulation.run_simulation_model(
            config_map[config],
            strategy_map[charging_strategy],
            independent_variables.p_cp_rated_uncoordinated_strategy
        )
        results = ModelResults(model, config_map[config], strategy_map[charging_strategy], obj_weights)

    else:
        model = build_model.BuildModel(
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy],
            obj_weights=obj_weights
        )
        opt_model = model.get_optimisation_model()

        # Solve model
        solved_model, calc_mip_gap = solve_model.solve_optimisation_model(
            opt_model,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap
        )

        # Save results
        results = ModelResults(solved_model, config_map[config], strategy_map[charging_strategy], obj_weights, calc_mip_gap)

    results.save_model_to_pickle(version=version)

    return results
