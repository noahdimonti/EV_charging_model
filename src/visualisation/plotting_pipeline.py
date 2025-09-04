from src.visualisation import economic_comparison, technical_comparison, social_comparison


def plot_all(configurations, charging_strategies, version, save_img=True):
    economic_comparison.num_cp_plot(
        configurations,
        charging_strategies,
        version,
        save_img
    )

    technical_comparison.demand_profiles_by_config(
        configurations,
        charging_strategies,
        version,
        save_img
    )
    technical_comparison.charging_strategy_load_delta_comparison(
        configurations,
        charging_strategies,
        version,
        save_img
    )

    social_comparison.soc_boxplot(
        configurations,
        charging_strategies,
        version,
        save_img
    )
    social_comparison.soc_distribution(
        configurations,
        charging_strategies,
        version,
        save_img
    )
    social_comparison.num_charging_day_plot(
        configurations,
        charging_strategies,
        version,
        save_img
    )

