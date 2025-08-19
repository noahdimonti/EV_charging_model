import os
import itertools
import pyomo.environ as pyo
import pandas as pd
from src.models.optimisation_models.build_model import BuildModel
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.models.utils.mapping import config_map, strategy_map
from src.config import params
from pprint import pprint


def get_lexicographic_optimal_solution(obj_priority_order: list, config: str, charging_strategy: str, version: str, tolerance=1e-4) -> dict:
    """
    Runs lexicographic optimisation for the given order of objectives.

    Args:
        model: Pyomo model with attributes '<obj>_objective'
        obj_priority_order: list of objectives in lexicographic priority order (e.g. ['economic', 'technical'])
        config: scenario parameter to build the model
        charging_strategy: scenario parameter to build the model
        version: scenario parameter to build the model
        tolerance: tolerance for 'keeping' previous optima (fraction of value)

    Returns:
        dict: optimal values for the given objective priority order
    """
    optimal_values = {}

    for i, obj in enumerate(obj_priority_order):
        print(f'\n--- Objective: {obj} ---')

        # Update version
        ver = f'{version}_{obj}_minimised'

        # Build model
        model_builder = BuildModel(
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy],
            version=ver,
        )
        model = model_builder.get_optimisation_model()

        # Set the current objective
        model.obj_function.set_value(
            expr=getattr(model, f'{obj}_objective')
        )

        # Add/update constraints for all previous objectives in the order
        for j in range(i):
            prev_obj = obj_priority_order[j]
            constraint_name = f'lex_constraint_{prev_obj}'
            optimal_val = optimal_values[prev_obj]
            expr = getattr(model, f'{prev_obj}_objective') <= optimal_val * (1 + tolerance)


            if hasattr(model, constraint_name):
                getattr(model, constraint_name).set_value(expr)
            else:
                setattr(model, constraint_name, pyo.Constraint(expr=expr))

        # Solve the model
        results = run_optimisation_model(
            config=config,
            charging_strategy=charging_strategy,
            version=ver,
            model=model,
            verbose=True,
            time_limit=20,
            mip_gap=1,
            save_model=True
        )

        if results is not None:
            raw, formatted = analyse_results(
                [config],
                [charging_strategy],
                ver,
                save_df=False,
            )
            print(formatted)

            # Store the optimal value for this objective
            val = results.objective_components.get(f'{obj}_objective')
            optimal_values[obj] = val
        else:
            print('\nResult is None\n')

    return optimal_values


def build_payoff_table(objectives: list, config: str, charging_strategy: str, version: str) -> dict:
    payoff_table = {}

    for primary in objectives:
        # Update version
        ver = version + f'_lex_{primary}_primary'

        # Put primary first, rest in any order
        secondary_objs = [o for o in objectives if o != primary]
        obj_order = [primary] + secondary_objs

        payoff_table[primary] = get_lexicographic_optimal_solution(
            obj_priority_order=obj_order,
            config=config,
            charging_strategy=charging_strategy,
            version=ver,
            tolerance=1e-4
        )

    return payoff_table


def compute_ranges_from_payoff(payoff_table):
    """
    payoff_table: dict like {primary: {obj: value, ...}, ...}
    returns: dict mapping objective -> range (max - min)
    """
    # Get objectives from first row
    objectives = []
    for row in payoff_table.values():
        objectives = list(row.keys())
        break

    ranges = {}

    for obj in objectives:
        vals = [payoff_table[row][obj] for row in payoff_table]
        r = max(vals) - min(vals)
        ranges[obj] = r

    return ranges


def generate_epsilon_grid(payoff_table, primary_obj, grid_points):
    """
    Generate epsilon combinations for secondary objectives.
    Returns list of dicts (each dict maps secondary_obj -> epsilon_value) and list of secondary_obj names.
    """
    sec_objs = [o for o in next(iter(payoff_table.values())).keys() if o != primary_obj]

    epsilon_values = {}
    # For each secondary objective, compute min and max across payoff table (rows are primary choices)
    for obj in sec_objs:
        vals = [payoff_table[row][obj] for row in payoff_table]
        obj_min, obj_max = min(vals), max(vals)

        # generate grid_points+1 values inclusive of extremes
        if grid_points <= 0:
            raise ValueError('grid_points must be >= 1')
        step = (obj_max - obj_min) / grid_points
        epsilon_values[obj] = [obj_max - (step * k) for k in range(grid_points + 1)]

    # Cartesian product of epsilon values
    combos = list(itertools.product(*[epsilon_values[o] for o in sec_objs]))
    epsilons = [dict(zip(sec_objs, c)) for c in combos]

    return epsilons, sec_objs


def augmecon_sweep(
        payoff_table,
        primary_obj,
        grid_points,
        config,
        charging_strategy,
        version,
        rho=1e-5,
        epsilon_tolerance_frac=1e-8,
        duplicate_tol=1e-6):
    """
    Augmented ε-constraint sweep.

    - payoff_table: dict from build_payoff_table (rows are primary objectives)
    - primary_obj: str name of primary objective (matches '<name>_objective' on model)
    - grid_points: int number of intervals per secondary objective
    - rho: augmentation coefficient (small positive)
    - epsilon_tolerance_frac: small relative tolerance when forming equality (keeps numerical robustness)
    - duplicate_tol: tolerance for considering two objective vectors identical

    Returns:
        list of dicts: each dict contains epsilon values and objective values for a found Pareto point
    """
    # 1) Compute ranges for augmentation scaling
    ranges = compute_ranges_from_payoff(payoff_table)

    # 2) Build epsilon grid
    epsilons, sec_objs = generate_epsilon_grid(payoff_table, primary_obj, grid_points)

    pareto_solutions = []
    infeasible_records = []
    violation_records = []
    seen = set()

    # List all objectives from payoff table
    all_objs = list(next(iter(payoff_table.values())).keys())

    for idx, eps in enumerate(epsilons):
        # --- Rebuild the model fresh each time ---
        ver = f'{version}_{primary_obj}_eps{idx}'
        model_builder = BuildModel(
            config=config_map[config],
            charging_strategy=strategy_map[charging_strategy],
            version=ver,
        )
        model = model_builder.get_optimisation_model()

        # 3) Set the primary objective
        prim_expr = getattr(model, f'{primary_obj}_objective')
        model.obj_function.set_value(expr=prim_expr)

        # 4) Add epsilon constraints for each secondary objective
        for sec in sec_objs:
            slack_name = f'aug_slack_{sec}'
            constr_name = f'aug_const_{sec}'

            # Slack variable
            setattr(model, slack_name, pyo.Var(domain=pyo.NonNegativeReals))
            slack_var = getattr(model, slack_name)

            # Set objective constraint using the slack variable
            eps_val = eps[sec]
            expr = (getattr(model, f'{sec}_objective') + slack_var == eps_val)
            setattr(model, constr_name, pyo.Constraint(expr=expr))

        # 5) Build augmented objective: primary + rho * sum(s_j / r_j)
        aug_terms = []
        for sec in sec_objs:
            slack_var = getattr(model, f'aug_slack_{sec}')
            r = ranges.get(sec, 0.0)
            denom = r if (r and r > 0.0) else 1.0
            aug_terms.append(slack_var / denom)

        if aug_terms:
            aug_obj_expr = prim_expr + (rho * sum(aug_terms))
        else:
            aug_obj_expr = prim_expr

        model.obj_function.set_value(expr=aug_obj_expr)

        # 6) Solve
        results = run_optimisation_model(
            config=config,
            charging_strategy=charging_strategy,
            version=ver,
            model=model,
            verbose=True,
            time_limit=10,
            mip_gap=1
        )

        if results is None:
            # Model failed to solve or raised error — treat as infeasible
            infeasible_records.append({
                'version': ver,
                'epsilon': eps.copy(),
                'termination_condition': 'No results returned (exception or failure)'
            })
            continue

        feasible = (
                results.termination_condition == pyo.TerminationCondition.optimal or
                results.termination_condition == pyo.TerminationCondition.feasible
        )

        if not feasible:
            infeasible_records.append({
                'version': ver,
                'epsilon': eps.copy(),
                'termination_condition': str(results.termination_condition)
            })
            continue

        # 7) Extract objective values
        sol = {}
        for obj in all_objs:
            val = results.objective_components.get(f'{obj}_objective')
            sol[obj] = val

        # 7b) Check for violations (shouldn't happen, but log if so)
        violations = {}
        tol_abs = 1e-8  # absolute tolerance for numeric noise
        for sec in sec_objs:
            eps_val = eps[sec]
            actual = sol[sec]
            # For minimisation, require actual <= eps_val + tol
            if actual > eps_val + tol_abs:
                violations[sec] = {
                    'eps': eps_val,
                    'actual': actual,
                    'excess': actual - eps_val
                }

        if violations:
            violation_records.append({
                'version': ver,
                'epsilon': eps.copy(),
                'objectives': sol.copy(),
                'violations': violations
            })
            # NOTE: we *do not* automatically discard solutions with tiny violation;
            # we log them so you can inspect and decide whether to tighten tolerances or increase rho.

        # 8) Duplicate detection
        key = tuple(round(sol[o], 8) for o in all_objs)
        if key in seen:
            continue
        seen.add(key)

        pareto_solutions.append({
            'version': ver,
            'epsilon': eps.copy(),
            'objectives': sol
        })

    # Save pareto solutions and infeasible records to csv
    pareto_df = pd.DataFrame([
        {'version': sol['version'], **sol['objectives']}
        for sol in pareto_solutions
    ])

    infeasible_df = pd.DataFrame([
        {'version': inf['version'], **inf['epsilon']}
        for inf in infeasible_records
    ])

    augmecon_path = os.path.join(params.data_output_path, 'augmecon_method')
    pareto_filename = f'{augmecon_path}/pareto_{config}_{charging_strategy}_{primary_obj}_primary_{grid_points}gp.csv'
    infeasible_filename = f'{augmecon_path}/infeasible_{config}_{charging_strategy}_{primary_obj}_primary_{grid_points}gp.csv'

    pareto_df.to_csv(pareto_filename)
    infeasible_df.to_csv(infeasible_filename)

    return pareto_solutions, infeasible_records


