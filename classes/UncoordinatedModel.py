import pandas as pd


class UncoordinatedModel:
    def __init__(self, name):
        self.name = name
        self.num_of_cps = 0
        self.p_ev_max = 0.0
        self.ev_load = pd.DataFrame()
        self.household_load = pd.DataFrame()
        self.grid = pd.DataFrame()
        self.total_load = pd.DataFrame()
