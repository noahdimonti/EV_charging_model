from src.models.utils.configs import CPConfig, ChargingStrategy

config_map = {
    'config_1': CPConfig.CONFIG_1,
    'config_2': CPConfig.CONFIG_2,
    'config_3': CPConfig.CONFIG_3,
}

strategy_map = {
    'uncoordinated': ChargingStrategy.UNCOORDINATED,
    'opportunistic': ChargingStrategy.OPPORTUNISTIC,
    'flexible': ChargingStrategy.FLEXIBLE
}


def validate_config_strategy(config: str, charging_strategy: str):
    if config not in config_map or charging_strategy not in strategy_map:
        raise ValueError("Invalid configuration or charging strategy.")
