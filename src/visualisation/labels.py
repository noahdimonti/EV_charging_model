

VERSION_LABELS = {
    'norm_w_sum': 'Socio-techno-economic',
    'min_economic': 'Economic',
    'min_technical': 'Technical',
    'min_econ_tech': 'Techno-economic',
}


def format_config_label(config: str) -> str:
    _, num = config.split('_')
    return f'Config {num}'


def format_strategy_label(strategy: str) -> str:
    return strategy.capitalize()


def format_version_label(version: str) -> str:
    return VERSION_LABELS.get(version, version)