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
        mip_gap=None) -> ModelResults:
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
        results.save_model_to_pickle(version=version)

        return results

    except Exception as e:
        print(f'{params.RED}An error occurred during optimisation: {e}.{params.RESET}')




# def solve_optimisation_model(model, version, solver='gurobi', verbose=False, time_limit=None, mip_gap=None):
#     """ MIP gap in percentage and time_limit in minutes """
#     solver = pyo.SolverFactory(solver)
#     print(f'\n=============================================================\n'
#           f'Solving {model.name} model ...'
#           f'\n=============================================================\n')
#
#     # Set time limit
#     time_limit_seconds = None
#     if time_limit is not None:
#         time_limit_seconds = time_limit * 60
#         solver.options['TimeLimit'] = time_limit_seconds
#
#     # Set MIP gap
#     if mip_gap is not None:
#         decimal_mip_gap = mip_gap / 100
#         solver.options['MIPGap'] = decimal_mip_gap
#
#     # Solver logs filepath
#     file_name = f'solver_log_{model.name}_{version}.log'
#     file_path = os.path.join(params.model_results_folder_path, 'solver_logs', file_name)
#
#     # Solve the model_data
#     start_time = time.time()
#     results = solver.solve(model, tee=verbose, logfile=file_path)
#     end_time = time.time()
#
#     # Solving time
#     solving_time = end_time - start_time
#
#     # Check solver status and termination condition
#     solver_status = results.solver.status
#     termination_condition = results.solver.termination_condition
#
#     # Print the status and termination condition
#     print(f'Solver Status: {solver_status}')
#     print(f'Termination Condition: {termination_condition}')
#
#     # Check if the solver was successful
#     try:
#         if solver_status == pyo.SolverStatus.ok and termination_condition == pyo.TerminationCondition.optimal:
#             print(f'{params.GREEN}Solver found an optimal solution.{params.RESET}')
#
#         # Check solver status for infeasibility
#         elif solver_status != pyo.SolverStatus.ok or termination_condition == pyo.TerminationCondition.infeasible:
#             print(f'{params.RED}Solver did not find an optimal solution.{params.RESET}')
#
#     except Exception as e:
#         print(f'{params.RED}An error occurred: {e}.{params.RESET}')
#
#     if (solving_time % 60) < 1:
#         print(f'\nModel solved in {solving_time:.3f} seconds')
#     else:
#         minutes = int(solving_time // 60)
#         remaining_seconds = solving_time % 60
#         print(f'\nModel solved in {minutes} minutes {remaining_seconds:.3f} seconds')
#
#     # Calculate MIP gap
#     upper_bound = results.problem.upper_bound
#     lower_bound = results.problem.lower_bound
#     calc_mip_gap = None
#
#     if upper_bound and lower_bound and upper_bound != 0:
#         calc_mip_gap = (abs(upper_bound - lower_bound) / abs(upper_bound)) * 100
#         print(f"Calculated MIP Gap: {calc_mip_gap:.4f}%")
#
#         # Information if solver is aborted
#         if time_limit is not None and mip_gap is not None:
#             if solving_time >= time_limit_seconds:
#                 print(f'\nSolver terminated due to time limit')
#             elif calc_mip_gap > mip_gap:
#                 print(f'\nMIP gap condition not met')
#
#     else:
#         print("Bounds not available for MIP gap calculation.")
#
#     print(f'-------------------------------------------------------------\n')
#
#     return model, calc_mip_gap
