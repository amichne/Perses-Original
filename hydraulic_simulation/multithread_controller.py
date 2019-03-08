import itertools
from math import ceil

import dask.threaded
from dask import compute, delayed, visualize


from hydraulic_simulation.data_util import CumulativeDistFailure,\
    TasMaxProfile, ComponentConfig, RepairPeriods
from hydraulic_simulation.controller import Controller
from hydraulic_simulation.data_util import ComponentConfig
from hydraulic_simulation.components import Pump, Pipe, Node, LinkType
from hydraulic_simulation.component_props import Exposure, Status


class StatisticalMTController(Controller):
    threads = int
    prev_timestep = int

    def __init__(self, threads, tasmax, years=82, timestep=60*60):
        self.threads = threads

        self.time = ((48 * 60 * 60) + (years * self.year))
        self.timestep = timestep
        self.prev_timestep = (0 - self.timestep)
        self.current_time = 0

        self.current_temp = 0.0
        self.tasmax = tasmax

        self.pumps = list()
        self.pipes = list()
        self.nodes = list()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return

    def populate(self, config, pumps, pvc, iron, motor_repair=25200, elec_repair=14400, pipe_repair=316800):
        uid = 0
        for i in range(pumps):
            self.pumps.append(
                Pump(uid, self.timestep, LinkType('elec'), run_epa=False))
            self.pumps[-1].exp_elec = Exposure(*config.exp_vals("elec", uid))
            self.pumps[-1].exp_motor = Exposure(*config.exp_vals("motor", uid))
            self.pumps[-1].status_elec = Status(elec_repair)
            self.pumps[-1].status_motor = Status(motor_repair)
            uid += 1
        for i in range(pvc):
            self.pipes.append(
                Pipe(uid, self.timestep, LinkType('pvc'), run_epa=False))
            self.pipes[-1].exp = Exposure(*config.exp_vals("pvc", uid))
            self.pipes[-1].status = Status(pipe_repair)
            uid += 1
        for i in range(iron):
            self.pipes.append(
                Pipe(uid, self.timestep, LinkType('iron'), run_epa=False))
            self.pipes[-1].exp = Exposure(*config.exp_vals("iron", uid))
            self.pipes[-1].status = Status(pipe_repair)
            uid += 1

    def run(self, failures, sql_yr_w):
        while True:
            if not self.iterate(failure_sql=failures, sql_yr_w=sql_yr_w):
                return

    def iterate(self, failure_sql, sql_yr_w):
        self.current_time += self.timestep
        self.prev_timestep += self.timestep

        if ((self.current_time - 86400) > self.prev_timestep):
            self.current_temp = self.tasmax.temp(self.current_time)

        if self.current_time % (self.year * sql_yr_w) == 0:
            print("{} year(s) done".format(str(sql_yr_w)))
            if failure_sql:
                self.failures_to_sql()

        self.increment_population(self.threads)

        if self.current_time >= self.time:
            return False
        return True

    def increment_population(self, chunks):
        ''' Allows multithreading - Note, not threading the pumps since there is comparitevely so few'''
        for pump in self.pumps:
            pump.bimodal_eval(self.current_temp, self.current_time)

        pipes = list()
        sections = section(self.pipes, chunks)
        for sect in sections:
            pipes.append(delayed_eval(sect,
                                      self.current_temp,
                                      self.current_time))
        self.pipes = list(itertools.chain(*dask.compute(*pipes)))


def section(data, n_sections):
    # looping till length l
    ret = list()
    step = ceil(len(data) / n_sections)
    for i in range(0, len(data), step):
        ret.append(data[i:i + step])
    return ret


def threaded_eval(pipe, temp, simtime):
    '''
    Evaluate exposure progression for TAS Max and Simtime:
        temp: float of tasmax in deg C
        simtime: int for current time of simulation in seconds'''
    pipe.exp, pipe.status = pipe.progression(
        pipe.exp, pipe.status, temp, simtime, pipe.type_)
    return pipe


@dask.delayed
def delayed_eval(pipes, temp, time):
    return [threaded_eval(pipe, temp, time) for pipe in pipes]
