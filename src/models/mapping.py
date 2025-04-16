from src.models.configs import CPConfig, ChargingStrategy

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