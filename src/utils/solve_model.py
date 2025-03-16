import time
import pyomo.environ as pyo
from src.config import params


def solve_optimisation_model(model, solver='gurobi', verbose=False, time_limit=None, mip_gap=None):
    """ MIP gap in percentage """
    solver = pyo.SolverFactory(solver)
    print(f'\n=========================================================\n'
          f'Solving {model.name} model ...'
          f'\n=========================================================\n')

    # Set time limit
    if time_limit is not None:
        solver.options['TimeLimit'] = time_limit

    # Set MIP gap
    elif mip_gap is not None:
        decimal_mip_gap = mip_gap / 100
        solver.options['MIPGap'] = decimal_mip_gap

    # Solve the model_data
    start_time = time.time()
    results = solver.solve(model, tee=verbose)
    end_time = time.time()

    # Solving time
    solving_time = end_time - start_time

    # Check solver status and termination condition
    solver_status = results.solver.status
    termination_condition = results.solver.termination_condition

    # Print the status and termination condition
    print(f'Solver Status: {solver_status}')
    print(f'Termination Condition: {termination_condition}')

    # Check if the solver was successful
    try:
        if solver_status == pyo.SolverStatus.ok and termination_condition == pyo.TerminationCondition.optimal:
            print(f'{params.GREEN}Solver found an optimal solution.{params.RESET}')

        # Check solver status for infeasibility
        elif solver_status != pyo.SolverStatus.ok or termination_condition == pyo.TerminationCondition.infeasible:
            print(f'{params.RED}Solver did not find an optimal solution.{params.RESET}')

    except Exception as e:
        print(f'{params.RED}An error occurred: {e}.{params.RESET}')

    print(f'\n---------------------------------------------------------')

    if (solving_time % 60) < 1:
        print(f'Model solved in {solving_time:.3f} seconds')
    else:
        minutes = int(solving_time // 60)
        remaining_seconds = solving_time % 60
        print(f'Model solved in {minutes} minutes {remaining_seconds:.3f} seconds')

    # Calculate MIP gap
    upper_bound = results.problem.upper_bound
    lower_bound = results.problem.lower_bound
    calc_mip_gap = None

    if upper_bound and lower_bound and upper_bound != 0:
        calc_mip_gap = (abs(upper_bound - lower_bound) / abs(upper_bound)) * 100
        print(f"Calculated MIP Gap: {calc_mip_gap:.4f}%")

        # Information that time is prioritised if both time_limit and mip_gap have values
        if time_limit is not None and mip_gap is not None:
            print(f'\nSolver terminated due to time limit')
            if calc_mip_gap > decimal_mip_gap:
                print(f'MIP gap condition not met')

    else:
        print("Bounds not available for MIP gap calculation.")

    print(f'---------------------------------------------------------\n')

    return model


def simulate_uncoordinated_model(model):
    print(f'\n=========================================================\n'
          f'Running {model.name} model ...'
          f'\n=========================================================\n')
