from src.config import params
from src.models.optimisation_models.build_model import BuildModel
from src.models.utils.log_model_info import log_with_runtime, print_runtime
from src.models.optimisation_models.optimisation_model import solve_model, log_solver_results
from src.models.utils.mapping import validate_config_strategy, config_map, strategy_map
from src.models.results.model_results import ModelResults


def run_optimisation_model(
        config: str,
        charging_strategy: str,
        version: str,
        obj_weights: dict[str, float],
        solver='gurobi',
        verbose=False,
        time_limit=None,
        mip_gap=None,
        save_model: bool = True) -> ModelResults:
    # Validate config and charging strategy
    validate_config_strategy(config, charging_strategy)

    # Build model constraints
    model_builder = BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy],
        obj_weights=obj_weights
    )
    model = model_builder.get_optimisation_model()

    # Define labels
    label = f'Solving {model.name} model'
    finished_label = 'Model solved'

    try:
        (solved_model, calc_mip_gap, solver_status, termination_condition), solving_time = log_with_runtime(
            label,
            finished_label,
            solve_model,
            model,
            version,
            solver_name=solver,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap
        )

        log_solver_results(
            solver_status,
            termination_condition,
            solving_time,
            calc_mip_gap,
            time_limit,
            mip_gap
        )

        print_runtime(finished_label, solving_time)

        # Save results
        results = ModelResults(solved_model, config_map[config], strategy_map[charging_strategy], obj_weights,
                               calc_mip_gap)

        # Save results to pickle
        if save_model:
            results.save_model_to_pickle(version=version)

        return results

    except Exception as e:
        print(f'{params.RED}An error occurred during optimisation: {e}.{params.RESET}')


