import pyomo.environ as pyo


def solve_optimisation_model(model, solver='gurobi', verbose=False):
    solver = pyo.SolverFactory(solver)
    print(f'\n=======================================================\n'
          f'Solving {model.name} model ...'
          f'\n=======================================================\n')
    solver_results = solver.solve(model, tee=verbose)

    # Define colours to differentiate whether optimal solution is found
    RESET = "\033[0m"  # Reset to default
    RED = '\033[31m'  # Red color (e.g., for warning or error)
    GREEN = '\033[32m'  # Green color (e.g., for success)

    # Check solver status and termination condition
    solver_status = solver_results.solver.status
    termination_condition = solver_results.solver.termination_condition

    # Print the status and termination condition
    print(f'Solver Status: {solver_status}')
    print(f'Termination Condition: {termination_condition}')

    # Check if the solver was successful
    try:
        if solver_status == pyo.SolverStatus.ok and termination_condition == pyo.TerminationCondition.optimal:
            print(f'{GREEN}Solver found an optimal solution.{RESET}')

        # Check solver status for infeasibility
        elif solver_status != pyo.SolverStatus.ok or termination_condition == pyo.TerminationCondition.infeasible:
            print(f'{RED}Solver did not find an optimal solution.{RESET}')

    except Exception as e:
        print(f'An error occurred: {e}.{RESET}')

    print(f'---------------------------------------------------------\n')


def simulate_uncoordinated_model(model):
    print(f'\n=======================================================\n'
          f'Running {model.name} model ...'
          f'\n=======================================================\n')
