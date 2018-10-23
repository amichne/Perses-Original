from typing import List
from ctypes import c_int, c_float, CDLL
import math

from data_util import CumulativeDistFailure
from epanet import et


class Status:
    repair_time: int
    functional: bool
    time_left: int

    def __init__(self, repair_time, functional=True, time_left=0):
        self.repair_time = repair_time
        self.functional = functional
        self.time_left = time_left

    def disable(self, index):
        self.functional = False
        self.time_left = self.repair_time
        et.ENsetlinkvalue(index, et.EN_STATUS, 0)

    def repair(self, timestep, index):
        self.time_left -= timestep
        if self.time_left <= 0:
            et.ENsetlinkvalue(index, et.EN_STATUS, 1)
            self.functional = True
        else:
            et.ENsetlinkvalue(index, et.EN_STATUS, 0)
            self.functional = False
        return self


class Exposure:
    ''' The coeff is a 1hr window. CDF is 
    assumed to be (degree Celcius) * year '''
    current: float = 0.0
    curr_god_fac: float
    index_god_fac: int = 0
    future_god_fac: List[float]
    cdf: CumulativeDistFailure
    coeff = float((1.0 / 365.0) / 24.0)

    def __init__(self, cdf, gf_list):
        self.cdf = cdf
        self.future_god_fac = gf_list
        self.god_factor = self.future_god_fac[self.index_god_fac]

    def increment(self, temp, duration):
        self.current += self.coeff * temp * duration

    def evaluation(self) -> bool:
        high = self.cdf[math.ceil(self.current)]
        low = self.cdf[math.floor(self.current)]
        percent_failure = ((high - low) * (self.current -
                                           math.floor(self.current))) + low
        if percent_failure > self.curr_god_fac:
            return False
        self.reset()
        return True

    def failure(self, temp, duration) -> bool:
        self.increment(temp, duration)
        return self.evaluation()

    def reset(self):
        self.current = 0.0
        self.index_god_fac += 1
        self.curr_god_fac = self.future_god_fac[self.index_god_fac]
