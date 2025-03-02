import pandas as pd
import os
from src.config import params


def get_household_load():
    # Get the absolute path of the project root directory
    # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    # Define the input data directory and file path relative to the project root
    household_load_dir = os.path.join('/Users/noahdimonti/Developer/PycharmProjects/EV_apartment_model', 'data/interim')
    household_load_file = f'load_profile_{params.num_of_days}_days_{params.num_of_households}_households.csv'
    household_load_path = os.path.join(household_load_dir, household_load_file)

    try:
        household_load = pd.read_csv(filepath_or_buffer=household_load_path, parse_dates=True, index_col=0)
        return household_load
    except FileNotFoundError:
        print(f'Warning: Household load file not found at {household_load_path}.')


if __name__ == '__main__':
    get_household_load()
