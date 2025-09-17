from src.visualisation.plot_comparison import economic_comparison, social_comparison, technical_comparison


def plot_all(configurations: list[str], charging_strategies: list[str], version: str, save_img=True):
    economic_comparison.num_cp_plot(
        configurations,
        charging_strategies,
        version,
        save_img
    )

    technical_comparison.get_dso_metrics_df(
        configurations,
        charging_strategies,
        version,
        'models_comparison'
    )

    social_comparison.soc_boxplot(
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
    social_comparison.wait_time_distribution(
        configurations,
        charging_strategies,
        version,
        save_img
    )

