import pandas as pd
import matplotlib.pyplot as plt
from collections import deque
from src.config import params, ev_params
from pprint import pprint


class UncoordinatedModelConfig3:
    def __init__(self,
                 ev_data: list,
                 household_load: pd.DataFrame,
                 p_cp_rated_scaled: float,
                 num_cp: int,
                 evs_to_cp_assignment: dict
                 ):
        self.ev_data = ev_data
        self.household_load = household_load
        self.p_cp_rated_scaled = p_cp_rated_scaled
        self.num_cp = num_cp
        self.evs_to_cp_assignment = evs_to_cp_assignment

    def run(self):
        # Assign EVs permanently to CPs

        pass











