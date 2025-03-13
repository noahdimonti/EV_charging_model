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
    OPPORTUNISTIC = 'opportunistic'
    FLEXIBLE = 'flexible'

    @classmethod
    def validate(cls, charging_strategy):
        if charging_strategy not in cls:
            allowed_values = [f"{cls.__name__}.{member.name}" for member in cls]  # Format as ChargingMode.DAILY_CHARGE
            raise ValueError(f"Invalid CP configuration: {charging_strategy}. Allowed values: {allowed_values}")


class MaxChargingPower(Enum):
    VARIABLE = 'variable'
    L_1_LESS = 1.3
    L_1 = 2.4
    L_2_SINGLE_PHASE = 3.7
    L_2_THREE_PHASE = 7.2

    @classmethod
    def validate(cls, charging_strategy, p_cp_max_mode):
        """Validate p_cp_rated_mode based on charging strategy."""
        if charging_strategy == ChargingStrategy.OPPORTUNISTIC:
            if p_cp_max_mode != cls.VARIABLE:
                raise ValueError(
                    f"For {charging_strategy.value}, p_cp_max must be VARIABLE, not {p_cp_max_mode.value}."
                )
        else:  # Other charging modes
            if p_cp_max_mode == cls.VARIABLE:
                raise ValueError(
                    f"For {charging_strategy.value}, p_cp_max cannot be VARIABLE. Choose a parameter value."
                )
