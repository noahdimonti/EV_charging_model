import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from src.config import params
from src.utils.model_results import ModelResults


def plot_all(version: str):
    pass


def plot_investment_costs(version, save_img=False):
    pass


def plot_dso_metrics_comparison(metrics, save_img=False):
    print(metrics['config_1_opportunistic'])



pd.set_option('display.max_columns', None)

plot_all('avgdist25km_without_f_fair')