import pyomo.environ as pyo
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
        obj_weights: dict[str|float],
        model: pyo.ConcreteModel = None,
        solver='gurobi',
        verbose=False,
        time_limit=None,
        mip_gap=None,
        thread_count=None,
        save_model: bool = True) -> ModelResults:
    # Validate config and charging strategy
    validate_config_strategy(config, charging_strategy)

    # Build model
    if model is None:
        model_builder = BuildModel(
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy],
            version=version,
            obj_weights=obj_weights
        )
        model = model_builder.get_optimisation_model()

    # Define labels
    label = f'Solving {model.name} model'
    finished_label = 'Model solved'

    try:
        (solved_model, calc_mip_gap, solver_status, termination_condition), solving_time = log_with_runtime(
            label,
            solve_model,
            model,
            version,
            solver_name=solver,
            verbose=verbose,
            time_limit=time_limit,
            mip_gap=mip_gap,
            thread_count=thread_count
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
        results = ModelResults(
            model=solved_model,
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy],
            mip_gap=calc_mip_gap,
            obj_weights=obj_weights
        )

        results.solver_status = solver_status
        results.termination_condition = termination_condition

        # Save results to pickle
        if save_model:
            results.save_model_to_pickle(version=version)

        return results

    except Exception as e:
        print(f'{params.RED}An error occurred during optimisation: {e}.{params.RESET}')
        return None


