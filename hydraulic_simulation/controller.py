from shutil import rmtree
from os import makedirs
import itertools
from hydraulic_simulation.db_util import DatabaseHandle
from hydraulic_simulation.data_util import CumulativeDistFailure, TasMaxProfile, ComponentConfig, RepairPeriods, chunk
from hydraulic_simulation.component_props import Exposure, Status
from hydraulic_simulation.components import Pump, Pipe, Node, LinkType
from hydraulic_simulation.threading_funcs import *
from epanettools import epanet2 as et
from dask import compute, delayed, visualize
import dask.threaded
from math import ceil
from copy import copy, deepcopy

PIPESPLIT = 20
dask.config.set(pool=dask.threaded.ThreadPool(PIPESPLIT))


class Controller:
    network = None
    tmp_dir = None
    tasmax = None
    pumps = None
    pipes = None
    nodes = None
    current_time = None
    current_temp = None
    timestep = None
    time = 0
    year = 60 * 60 * 24 * 365
    db_handle = None

    def __init__(self, network, output, tasmax, years=82, timestep=60*60, tmp_dir='data/tmp/', epa=True):
        ''' Initializes the EPANET simulation, as well adding a two day
            buffer to the network file, and saving in a temp location.
            This temp network with the buffer will be deleted upon class
            destruction.
        '''
        self.epa = epa
        self.timestep = timestep
        self.time = ((48 * 60 * 60) + (years * self.year))
        if epa:
            self.tmp_dir = tmp_dir
            try:
                rmtree(self.tmp_dir)
            except Exception:
                pass
            makedirs(tmp_dir)
            et.ENopen(network, output, '')
            et.ENsettimeparam(0, self.time)
            network = tmp_dir + network.split('/')[-1]
            output = tmp_dir + output.split('/')[-1]
            et.ENsaveinpfile(network)
            et.ENclose()
            et.ENopen(network, output, '')
            self.network = network
        self.tasmax = tasmax
        self.pumps = list()
        self.pipes = list()
        self.nodes = list()
        self.current_time = 0
        self.current_temp = 0.0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.epa:
            rmtree(self.tmp_dir)

    def populate_epa(self, conf: ComponentConfig, node_types=[et.EN_JUNCTION], motor_repair=25200, elec_repair=14400, pipe_repair=316800):
        for i in range(1, et.ENgetcount(et.EN_NODECOUNT)[1]+1):
            self.nodes.append(Node(i))

        for i in range(1, et.ENgetcount(et.EN_LINKCOUNT)[1]+1):
            link_type = et.ENgetlinktype(i)[1]
            if link_type in [et.EN_PIPE, et.EN_CVPIPE]:
                rough = et.ENgetlinkvalue(i, et.EN_ROUGHNESS)[1]
                if rough > 140:
                    self.pipes.append(
                        Pipe(i, self.timestep, LinkType('iron')))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("iron", i))
                else:
                    self.pipes.append(
                        Pipe(i, self.timestep, LinkType('pvc')))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("pvc", i))
                self.pipes[-1].status = Status(pipe_repair)
            elif link_type == et.EN_PUMP:
                self.pumps.append(
                    Pump(i, self.timestep, LinkType('pump')))
                self.pumps[-1].exp_elec = Exposure(*conf.exp_vals("elec", i))
                self.pumps[-1].exp_motor = Exposure(*conf.exp_vals("motor", i))
                self.pumps[-1].status_elec = Status(elec_repair)
                self.pumps[-1].status_motor = Status(motor_repair)

    def run(self, failures, pressure, sql_yr_w):
        et.ENopenH()
        et.ENinitH(0)

        # Run for two days to create network equilibrium
        time = et.ENrunH()[1]
        while time < 172800:
            et.ENnextH()[1]
            time = et.ENrunH()[1]

        while True:
            if not self.iterate_epa(failure_sql=failures, pressure_sql=pressure, sql_yr_w=sql_yr_w):
                et.ENcloseH()
                et.ENclose()
                return

    def iterate_epa(self, failure_sql, pressure_sql, sql_yr_w):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            for node_ in self.nodes:
                node_.save_pressure(self.current_time)
            if time % (self.year * sql_yr_w) == 0:
                print("{} year(s) done".format(str(sql_yr_w)))
                if pressure_sql:
                    self.pressure_to_sql()
                if failure_sql:
                    self.failures_to_sql()
                # self.write_sql()
            self.increment_population()

        if et.ENnextH()[1] <= 0:
            return False
        return True

    def increment_population(self):
        for pump_ in self.pumps:
            pump_.bimodal_eval(self.current_temp, self.current_time)
        for pipe_ in self.pipes:
            pipe_.eval(self.current_temp, self.current_time)

    def populate_non_epa(self, config, pumps, pvc, iron, motor_repair=25200, elec_repair=14400, pipe_repair=316800):
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

    def run_no_epa(self, failures, sql_yr_w):
        while True:
            if not self.iterate_no_epa(failure_sql=failures, sql_yr_w=sql_yr_w):
                return

    def iterate_no_epa(self, failure_sql, sql_yr_w):
        self.current_time += self.timestep

        if (self.current_time % 86400 == 0):
            self.current_temp = self.tasmax.temp(self.current_time)

        if self.current_time % (self.year * sql_yr_w) == 0:
            print("{} year(s) done".format(str(sql_yr_w)))
            if failure_sql:
                self.failures_to_sql()

        self.threaded_increment_pop(PIPESPLIT)

        if self.current_time >= self.time:
            return False
        return True

    def threaded_increment_pop(self, chunks):
        ''' Allows multithreading - Note, not threading the pumps since there is comparitevely so few'''
        pipe_chunks = chunk(self.pipes, chunks)
        pipes = list()
        for i in range(len(pipe_chunks)):
            pipes.append(chunked_pipes(pipe_chunks[i],
                                       self.current_temp,
                                       self.current_time))
        for i in range(len(self.pumps)):
            self.pumps[i].bimodal_eval(self.current_temp, self.current_time)
        self.pipes = list(itertools.chain(*dask.compute(*pipes)))

    def create_db(self, db_handle: DatabaseHandle, pressure=True, failure=True, outages=True):
        self.db_handle = db_handle
        self.db_handle.reset_db()

        if pressure:
            pressure_schema = '(node_id CHAR(5), pressure DOUBLE, time INT UNSIGNED)'
            self.db_handle.create_table('pressure', pressure_schema)

        if failure:
            failure_schema = '(link_id CHAR(5), time INT UNSIGNED, type char(5))'
            self.db_handle.create_table('failure', failure_schema)

        if outages:
            outage_schema = '(link_id CHAR(5), time INT UNSIGNED, type char(5))'
            self.db_handle.create_table('outage', outage_schema)

        print("Table created for run: " + self.db_handle.db)

    def pressure_to_sql(self):
        tmp_pres = list()
        for node_ in self.nodes:
            tmp_pres.extend(node_.pressure)
            node_.pressure.clear()
        for index in range(len(tmp_pres)):
            tmp_pres[index][2] = tmp_pres[index][2] / self.timestep
        self.db_handle.insert(tmp_pres, 'pressure',
                              '(node_id, pressure, time)')

    def failures_to_sql(self):
        tmp_lnk = list()
        for link_ in (self.pipes+self.pumps):
            tmp_lnk.extend(link_.failure)
            link_.failure.clear()
        for index in range(len(tmp_lnk)):
            tmp_lnk[index][1] = tmp_lnk[index][1] / self.timestep

        self.db_handle.insert(tmp_lnk, 'failure', '(link_id, time, type)')
