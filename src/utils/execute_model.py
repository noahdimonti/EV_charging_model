import pyomo.environ as pyo
import matplotlib.pyplot as plt
from src.models.optimisation_models import build_model, configs
from src.config import params
from src.utils import solve_model
from src.utils.evaluation_metrics import EvaluationMetrics
from src.utils.model_results import ModelResults


def plot_results(model):
    soc_data = {i: [pyo.value(model.soc_ev[i, t]) for t in model.TIME] for i in model.EV_ID}
    p_ev_data = {i: [pyo.value(model.p_ev[i, t]) for t in model.TIME] for i in model.EV_ID}

    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(5, 10), sharex=True)

    for i in model.EV_ID:
        axes[0].plot(params.timestamps, p_ev_data[i], linestyle='-', label=f'EV_{i}')
        axes[1].plot(params.timestamps, soc_data[i], linestyle='-', label=f'EV_{i}')

    axes[0].set_ylabel('Charging Power (kW)')
    axes[1].set_ylabel('SOC (kWh)')
    axes[0].legend()
    axes[1].legend()

    # Common X label
    axes[-1].set_xlabel("Time Steps")

    # Add title
    fig.suptitle(f'{model.name}', fontsize=16)

    # Adjust layout
    plt.tight_layout(pad=3)

    plt.show()


def run_model(config: str,
              charging_strategy: str,
              verbose=False,
              time_limit=None,
              mip_gap=None):

    config_map = {
        'config_1': configs.CPConfig.CONFIG_1,
        'config_2': configs.CPConfig.CONFIG_2,
        'config_3': configs.CPConfig.CONFIG_3,
    }

    strategy_map = {
        'opportunistic': configs.ChargingStrategy.OPPORTUNISTIC,
        'flexible': configs.ChargingStrategy.FLEXIBLE
    }

    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid config or charging strategy.")

    model = build_model.BuildModel(
        config=config_map[config],
        charging_strategy=strategy_map[charging_strategy]
    )
    opt_model = model.get_optimisation_model()

    # Solve model_data
    solved_model = solve_model.solve_optimisation_model(
        opt_model,
        verbose=verbose,
        time_limit=time_limit,
        mip_gap=mip_gap
    )

    # Save model results
    results = ModelResults(solved_model, config_map[config], strategy_map[charging_strategy])
    results.save_model_to_pickle()

    return results




