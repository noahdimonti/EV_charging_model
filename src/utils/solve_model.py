import time
import pyomo.environ as pyo
from src.config import params


def solve_optimisation_model(model, solver='gurobi', verbose=False):
    solver = pyo.SolverFactory(solver)
    print(f'\n=========================================================\n'
          f'Solving {model.name} model ...'
          f'\n=========================================================\n')
    start_time = time.time()
    solver_results = solver.solve(model, tee=verbose)
    end_time = time.time()
    solving_time = end_time - start_time

    # Check solver status and termination condition
    solver_status = solver_results.solver.status
    termination_condition = solver_results.solver.termination_condition

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

    print(f'---------------------------------------------------------\n')


def simulate_uncoordinated_model(model):
    print(f'\n=========================================================\n'
          f'Running {model.name} model ...'
          f'\n=========================================================\n')
