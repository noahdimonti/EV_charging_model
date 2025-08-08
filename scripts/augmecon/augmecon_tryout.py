import os
import itertools
import pyomo.environ as pyo
import pandas as pd
from src.models.optimisation_models.build_model import BuildModel
from src.models.optimisation_models.run_optimisation import run_optimisation_model
from scripts.experiments_pipeline.analyse_results import analyse_results
from src.models.utils.mapping import config_map, strategy_map
from src.config import params
from src.visualisation.epsilon_sweep_plot import plot_epsilon
from pprint import pprint


def main():
    config = 'config_1'
    charging_strategy = 'opportunistic'
    version = 'augmecon_test'
    objectives_priority = [
        'economic',
        'technical',
        'social'
    ]

    # Build model constraints
    model_builder = BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy],
        version=version,
    )
    model = model_builder.get_optimisation_model()

    payoff = build_payoff_table(
        model=model,
        objectives=objectives_priority,
        config=config,
        charging_strategy=charging_strategy,
        version=version,
    )

    pprint(payoff)



def get_lexicographic_optimal_solution(model, obj_priority_order, config, charging_strategy, version, epsilon=1e-4):
    """
    Runs lexicographic optimisation for the given order of objectives.
    Useful for building a Pareto-optimal payoff table row.

    Args:
        model: Pyomo model with attributes '<obj>_objective'
        obj_priority_order: list of objectives in lexicographic priority order (e.g. ['economic', 'technical'])
        config, charging_strategy, version: scenario parameters for your solver
        epsilon: tolerance for 'keeping' previous optima (fraction of value)

    Returns:
        dict: optimal values for the given objective priority order
    """
    optimal_values = {}

    for i, obj in enumerate(obj_priority_order):
        print(f'\n--- Objective: {obj} ---')
        # Set the current objective
        model.obj_function.set_value(
            expr=getattr(model, f'{obj}_objective')
        )

        # Add/update constraints for all previous objectives in the order
        for j in range(i):
            print(f'\nPrevious objective: {obj_priority_order[j]}')
            prev_obj = obj_priority_order[j]
            constraint_name = f'lex_constraint_{prev_obj}'
            optimal_val = optimal_values[prev_obj]
            print(f'Optimal value: {optimal_val}')
            expr = getattr(model, f'{prev_obj}_objective') <= optimal_val * (1 + epsilon)

            if hasattr(model, constraint_name):
                getattr(model, constraint_name).set_value(expr)
            else:
                setattr(model, constraint_name, pyo.Constraint(expr=expr))

        # Solve the model
        results = run_optimisation_model(
            config=config,
            charging_strategy=charging_strategy,
            version=version + f'_lex_{obj}_primary',
            model=model,
            verbose=True
        )

        raw, formatted = analyse_results(
            [config],
            [charging_strategy],
            version,
            save_df=False,
        )
        print(formatted)

        # Store the optimal value for this objective
        val = results.objective_components.get(f'{obj}_objective')
        optimal_values[obj] = val

    return optimal_values


def build_payoff_table(model, objectives, config, charging_strategy, version):
    payoff_table = {}

    for primary in objectives:
        # Put primary first, rest in any order (can choose fixed order for consistency)
        secondary_objs = [o for o in objectives if o != primary]
        obj_order = [primary] + secondary_objs

        payoff_table[primary] = get_lexicographic_optimal_solution(
            model=model,
            obj_priority_order=obj_order,
            config=config,
            charging_strategy=charging_strategy,
            version=version,
            epsilon=1e-4
        )

    return payoff_table



import itertools
import numpy as np
import pyomo.environ as pyo

def compute_ranges_from_payoff(payoff_table):
    """
    payoff_table: dict like {primary: {obj: value, ...}, ...}
    returns: dict mapping objective -> range (max - min)
    """
    objectives = list(next(iter(payoff_table.values())).keys())
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
            raise ValueError("grid_points must be >= 1")
        step = (obj_max - obj_min) / grid_points
        epsilon_values[obj] = [obj_min + step * k for k in range(grid_points + 1)]

    # Cartesian product of epsilon values
    combos = list(itertools.product(*[epsilon_values[o] for o in sec_objs]))
    epsilons = [dict(zip(sec_objs, c)) for c in combos]
    return epsilons, sec_objs


def augmecon_sweep_augmented(
        model,
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

    - model: a constructed Pyomo ConcreteModel (all variables/expressions already defined)
    - payoff_table: dict from build_payoff_table (rows are primary objectives)
    - primary_obj: str name of primary objective (matches '<name>_objective' on model)
    - grid_points: int number of intervals per secondary objective
    - rho: augmentation coefficient (small positive)
    - epsilon_tolerance_frac: small relative tolerance when forming equality (keeps numerical robustness)
    - duplicate_tol: tolerance for considering two objective vectors identical

    Returns:
        list of dicts: each dict contains objective values for all objectives at a found Pareto point
    """
    # 1) compute ranges r_j
    ranges = compute_ranges_from_payoff(payoff_table)

    # 2) build epsilon grid
    epsilons, sec_objs = generate_epsilon_grid(payoff_table, primary_obj, grid_points)

    pareto_solutions = []
    seen = set()

    # ensure objective component exists on model (a Pyomo Expression per objective)
    all_objs = list(next(iter(payoff_table.values())).keys())

    for idx, eps in enumerate(epsilons):
        # 3) set primary objective
        prim_expr = getattr(model, f"{primary_obj}_objective")
        model.obj_function.set_value(expr=prim_expr)

        # 4) For each secondary objective, create/update slack var and equality constraint:
        #    f_j(x) - s_j == eps_j
        for sec in sec_objs:
            slack_name = f"aug_slack_{sec}"
            constr_name = f"aug_eps_eq_{sec}"

            # create slack var if not existing
            if not hasattr(model, slack_name):
                setattr(model, slack_name, pyo.Var(domain=pyo.NonNegativeReals))
            slack_var = getattr(model, slack_name)

            # build equality expression f_j(x) - s_j == eps_j
            # Add tiny absolute tolerance to RHS to reduce infeasibility due to floating rounding
            eps_val = eps[sec]
            tol = epsilon_tolerance_frac * max(1.0, abs(eps_val))
            expr = (getattr(model, f"{sec}_objective") - slack_var == eps_val + tol*0.0)
            # We include tol*0.0 as placeholder; we will not actually change eps in equality, using exact eps

            # The correct equality (no tolerance in the equation itself) is:
            expr = (getattr(model, f"{sec}_objective") - slack_var == eps_val)

            # set or add constraint
            if hasattr(model, constr_name):
                getattr(model, constr_name).set_value(expr)
            else:
                setattr(model, constr_name, pyo.Constraint(expr=expr))

        # 5) Build augmented objective: primary + rho * sum(s_j / r_j)
        #    Avoid division by zero: if r_j == 0 -> use denom = 1.0 (effectively no scaling)
        aug_terms = []
        for sec in sec_objs:
            slack_var = getattr(model, f"aug_slack_{sec}")
            r = ranges.get(sec, 0.0)
            denom = r if (r and r > 0.0) else 1.0
            aug_terms.append(slack_var / denom)
        if len(aug_terms) > 0:
            aug_obj_expr = prim_expr + rho * sum(aug_terms)
        else:
            aug_obj_expr = prim_expr  # no secondaries (degenerate)

        # set the augmented objective (overwrite the existing objective expression)
        model.obj_function.set_value(expr=aug_obj_expr)

        # 6) solve
        results = run_optimisation_model(
            config=config,
            charging_strategy=charging_strategy,
            version=f"{version}_{primary_obj}_eps{idx}",
            model=model,
            verbose=False
        )

        # if solver didn't return objective values, skip
        sol = {}
        feasible = (results.solver.termination_condition == pyo.TerminationCondition.optimal or
                    results.solver.termination_condition == pyo.TerminationCondition.feasible)
        if not feasible:
            # log/skip infeasible combos
            # optionally store infeasible record
            continue

        # 7) extract objective values (actual values, not eps)
        for obj in all_objs:
            val = results.objective_components.get(f"{obj}_objective")
            sol[obj] = val

        # 8) early exit / duplicate detection
        # Round or quantize values for robust hashing
        key = tuple(round(sol[o], 8) for o in all_objs)
        if key in seen:
            # duplicate solution — skip storing
            continue
        seen.add(key)
        pareto_solutions.append({
            'epsilon': eps.copy(),
            'objectives': sol
        })

    return pareto_solutions




if __name__ == '__main__':
    main()