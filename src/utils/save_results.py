import json


def save_eval_metrics_results(economic_metric: dict, technical_metric: dict, social_metric: dict, filename: str):
    # Combine metrics in a dictionary
    metrics_data = {
        'economic_metrics': economic_metric,
        'technical_metrics': technical_metric,
        'social_metrics': social_metric
    }

    # Save to a json file
    with open(f'../../reports/{filename}.json', 'w') as f:
        json.dump(metrics_data, f, indent=4)



