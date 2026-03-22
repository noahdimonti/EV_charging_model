from enum import Enum


class CPConfig(Enum):
    CONFIG_1 = 'config_1'
    CONFIG_2 = 'config_2'
    CONFIG_3 = 'config_3'

    @classmethod
    def validate(cls, config):
        if config not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as CPConfig.CONFIG_1
            raise ValueError(f"Invalid CP configuration: {config}. Allowed values: {allowed_values}")


class ChargingStrategy(Enum):
    UNCOORDINATED = 'uncoordinated'
    OPPORTUNISTIC = 'opportunistic'
    FLEXIBLE = 'flexible'

    @classmethod
    def validate(cls, charging_strategy):
        if charging_strategy not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as ChargingMode.DAILY_CHARGE
            raise ValueError(f"Invalid CP configuration: {charging_strategy}. Allowed values: {allowed_values}")
