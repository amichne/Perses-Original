import pandas as pd
import numpy as np


def create_gfs(n, d):
    return pd.DataFrame([pd.Series(np.random.uniform(0, 1, d))
                         for x in range(n)])


class Config:
    sim_name = None
    temp = None

    motor_config = None
    elec_config = None
    iron_config = None
    pvc_config = None

    def __init__(self, sim_name=None, temp=None):
        self.sim_name = sim_name
        self.temp = temp


class ComponentConfig:
    name = None
    n = None
    repair_time = None
    cdf = None
    gf = None

    def __init__(self, name=None, n=None, repair_time=None, cdf=None, gf=None):
        self.name = name
        self.n = n
        self.repair_time = repair_time
        self.cdf = cdf
        self.gf = gf


class Cdf:
    data = None

    def __init__(self, filename):
        with open(filename, 'r') as handle:
            self.data = pd.Series(np.array([float(x)
                                            for x in handle.read().splitlines()]))


class Temperature:
    data = None

    def __init__(self, filename):
        with open(filename, 'r') as handle:
            self.data = pd.Series(handle.read().splitlines())
