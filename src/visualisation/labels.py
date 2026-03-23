

VERSION_LABELS = {
    'balanced': 'Socio-techno-economic',
    'min_econ': 'Economic',
    'min_tech': 'Technical',
    'min_soc': 'Social',
    'econ_tech': 'Techno-economic',
    'econ_soc': 'Socio-economic',
    'tech_soc': 'Socio-technical',
}


def format_config_label(config: str) -> str:
    _, num = config.split('_')
    return f'Configuration {num}'


def format_strategy_label(strategy: str) -> str:
    return strategy.capitalize()


def format_version_label(version: str) -> str:
    return VERSION_LABELS.get(version, version)