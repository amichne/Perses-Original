from random import random
from math import ceil, floor
import numpy as np
import pandas as pd
import numba
from numba import prange, njit


class ComponentPopulation:
    name = ''
    n = None
    god_factor = None
    exposure = None
    status = None
    cdf = None

    failures = list()
    coeff = float((((1.0 / 365.0) / 24.0) / 60.0) / 60.0)

    def __init__(self, name, n, cdf):
        ''' String indicating component type'''
        self.name = name
        self.n = pd.Series([i for i in range(n)])
        self.god_factor = pd.Series(np.zeros(n))
        self.cdf = cdf.data

    def populate(self, repair_time, depth=None, gf=None):
        self.vec_exposure = np.vectorize(self.exposure_vectorized)
        self.vec_failure = np.vectorize(self.fail_component, otypes=[])
        self.exposure = Exposure(self.n.size, depth, gf)
        self.status = Status(self.n.size, repair_time)
        for index in range(self.n.size):
            self.god_factor.iat[index] =\
                self.exposure.god_factor.iat[index,
                                             int(self.exposure.gf_index.iat[index])]

    def increment_vectorized(self, temperature, duration, time):
        self.status.values = np.where(self.status.values > 0,
                                      self.status.values - self.status.repair_time,
                                      0)
        expose = (temperature * duration * self.coeff)
        self.exposure.values = pd.eval('self.exposure.values + expose')
        per_failed = self.vec_exposure(self.exposure.values)
        failures = self.n[pd.eval('per_failed > self.god_factor')]
        if failures.size > 0:
            self.vec_failure(failures, time)

    def exposure_vectorized(self, exposure):
        high = self.cdf.iat[ceil(exposure)]
        low = self.cdf.iat[floor(exposure)]
        return (low + ((high - low) * (exposure - floor(exposure))))

    # @njit(parallel=True)
    # def exposure_njit(self, exposures: pd.DataFrame):

    #     for i in prange(self.n.size):
    #         high = self.cdf.iat[ceil(exposures.iat[i])]
    #         low = self.cdf.iat[floor(exposures.iat[i])]
    #         percent = low + ((high - low) *
    #                          (exposures.iat[i] - floor(exposures.iat[i])))

    # @njit(parallel=True)
    # def fail_components_njit(self, compoents):
    #     pass

    def fail_component(self, index, time):
        print(f'{self.name} index: {index} failed at time={time}')
        self.status.values[index] = self.status.repair_time
        self.exposure.values.iat[index] = 0
        self.exposure.gf_index.iat[index] += 1
        self.god_factor.iat[index] = self.exposure.god_factor.iat[index,
                                                                  int(self.exposure.gf_index.iat[index])]
        self.failures.append(f'{self.name}, {index}, {time}\n')

    def write_failure(self, filename, directory):
        with open(directory+filename, 'w+') as handle:
            handle.writelines(self.failures)


class Exposure:
    values = None
    god_factor = None
    gf_index = None

    def __init__(self, n, depth=None, gf=None):
        ''' values: each component exposure in current lifetime
            god_factor: God-Factors of depth=d, for n components
            gf_index: depth of current GF for each component
                        when failure occurs at component=i,
                        indexes[i] += 1 '''
        self.values = pd.Series(np.zeros(n))
        self.god_factor = gf
        self.gf_index = pd.Series(np.ones(n))


class Status:
    repair_time = None
    values = None

    def __init__(self, n, repair_time):
        ''' values: 0 indicates component is functional
                any value >= 0 equals the seconds left
                on the repair of the component'''
        self.values = pd.Series(np.zeros(n), dtype=np.int32)
        self.repair_time = repair_time

    def evaluate(self, index, duration):
        if self.values.iat[index] > 0:
            self.values.iat[index] -= duration
            return False
        return True
