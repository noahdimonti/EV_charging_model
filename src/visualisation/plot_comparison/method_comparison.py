import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.config import params
from src.visualisation import plot_setups
from src.visualisation.plot_comparison import social_comparison
from src.visualisation.plot_comparison.social_comparison import get_wait_time_list
from pprint import pprint


def plot_method_comparison(configurations: list[str], charging_strategies: list[str], methods: list[str], save_img=False):
    dfs = []
