import pyomo.environ as pyo
import os
from src.config import params


def solve_model(model, version, solver_name='gurobi', verbose=False, time_limit=None, mip_gap=None, thread_count=None):
    """Returns: (results, mip_gap, solver_status, termination_condition)"""
    solver = pyo.SolverFactory(solver_name)

    # Set options
    if time_limit is not None:
        solver.options['TimeLimit'] = time_limit * 60
    if mip_gap is not None:
        solver.options['MIPGap'] = mip_gap / 100

    # Log path
    file_name = f'solver_log_{model.name}_{version}.log'
    file_path = os.path.join(params.model_results_folder_path, 'solver_logs', file_name)

    # Set thread count
    if thread_count is not None:
        solver.options['Threads'] = thread_count

    # Set solver parameters
    solver.options['MIPFocus'] = 1  # Focus on finding good feasible solutions
    solver.options['Heuristics'] = 0.5  # More aggressive heuristics
    solver.options['Presolve'] = 2  # Aggressive presolve
    solver.options['Cuts'] = 2  # Aggressive cut generation
    solver.options['NodeMethod'] = 2  # Try barrier method at nodes for LP relaxation
    solver.options['ImproveStartTime'] = 60  # Wait time before aggressive improvement heuristics
    solver.options['Aggregate'] = 1  # Aggregate constraints to strengthen LP relaxation
    solver.options['RINS'] = 10
    solver.options['PumpPasses'] = 20

    # Solve model
    results = solver.solve(model, tee=verbose, logfile=file_path)

    # Extract info
    solver_status = results.solver.status
    termination_condition = results.solver.termination_condition

    # MIP gap calculation
    upper_bound = results.problem.upper_bound
    lower_bound = results.problem.lower_bound
    calc_mip_gap = None

    if upper_bound and lower_bound and upper_bound != 0:
        calc_mip_gap = (abs(upper_bound - lower_bound) / abs(upper_bound)) * 100

    return model, calc_mip_gap, solver_status, termination_condition


def log_solver_results(solver_status, termination_condition, solving_time, calc_mip_gap, time_limit=None, mip_gap=None):
    # Log status
    print(f'Solver Status: {solver_status}')
    print(f'Termination Condition: {termination_condition}')

    if solver_status == pyo.SolverStatus.ok and termination_condition == pyo.TerminationCondition.optimal:
        print(f'{params.GREEN}Solver found an optimal solution.{params.RESET}')
    elif solver_status != pyo.SolverStatus.ok or termination_condition == pyo.TerminationCondition.infeasible:
        print(f'{params.RED}Solver did not find an optimal solution.{params.RESET}')

    # MIP gap
    if calc_mip_gap is not None:
        print(f'\nCalculated MIP Gap: {calc_mip_gap:.4f}%\n')

        # Info if solver terminated early
        if time_limit is not None and mip_gap is not None:
            if solving_time >= time_limit * 60:
                print('Solver terminated due to time limit.\n')
            elif calc_mip_gap > mip_gap:
                print('MIP gap condition not met.\n')
    else:
        print('\nBounds not available for MIP gap calculation.\n')
