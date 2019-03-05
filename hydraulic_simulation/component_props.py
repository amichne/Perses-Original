from typing import List
from ctypes import c_int, c_float, CDLL
import math

from hydraulic_simulation.data_util import CumulativeDistFailure
from epanettools import epanet2 as et


class Status:
    repair_time = None
    functional = None
    time_left = None

    def __init__(self, repair_time, functional=True, time_left=0):
        self.repair_time = repair_time
        self.functional = functional
        self.time_left = time_left

    def disable(self, index, epa):
        self.functional = False
        self.time_left = self.repair_time
        if epa:
            et.ENsetlinkvalue(index, et.EN_STATUS, 0)

    def repair(self, index, timestep, epa):
        self.time_left -= timestep
        if self.time_left <= 0:
            if epa:
                et.ENsetlinkvalue(index, et.EN_STATUS, 1)
            self.functional = True
        else:
            if epa:
                et.ENsetlinkvalue(index, et.EN_STATUS, 0)
            self.functional = False
        return self


class Exposure:
    ''' The coeff is a 1hr window. CDF is
    assumed to be (degree Celcius) * year '''
    current = None
    curr_god_factor = None
    index_god_fac = None
    future_god_fac = list()
    cdf = CumulativeDistFailure
    # Yearly exposure transitioned to seconds
    coeff = float((((1.0 / 365.0) / 24.0) / 60.0) / 60.0)

    def __init__(self, cdf, gf_list):
        self.cdf = cdf
        self.current = 0.0
        self.index_god_fac = 0
        self.future_god_fac = gf_list
        self.curr_god_factor = self.future_god_fac[self.index_god_fac]

    def increment(self, temp, duration):
        self.current += self.coeff * temp * duration

    def failure_detected(self):
        high = self.cdf.values[math.ceil(self.current)]
        low = self.cdf.values[math.floor(self.current)]

        percent_failure = ((high - low) * (self.current -
                                           math.floor(self.current))) + low
        if percent_failure > self.curr_god_factor:
            self.reset()
            return True
        return False

    def failure(self, temp, duration):
        self.increment(temp, duration)
        return self.failure_detected()

    def reset(self):
        self.current = 0.0
        self.index_god_fac += 1
        self.curr_god_factor = self.future_god_fac[self.index_god_fac]
