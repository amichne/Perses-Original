from epanettools import epanet2 as et

from components import Pump, Pipe, Node, LinkType
from component_props import Exposure, Status
from data_util import CumulativeDistFailure, TasMaxProfile, ComponentConfig
from db_util import DatabaseHandle

from os import makedirs, removedirs
from shutil import rmtree


class Controller:
    network = None
    tmp_dir = None
    tasmax = None
    pumps = None
    pipes = None
    nodes = None
    current_time = None
    current_temp = None
    timestep = 60 * 60
    time = 0
    year = 60 * 60 * 24 * 365
    db_handle = None

    def __init__(self, network, output, tasmax, years=82, tmp_dir='data/tmp/'):
        ''' Initializes the EPANET simulation, as well adding a two day
            buffer to the network file, and saving in a temp location.
            This temp network with the buffer will be deleted upon class
            destruction.
        '''
        self.time = ((48 * 60 * 60) + (years * self.year))
        self.tmp_dir = tmp_dir
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
        rmtree(self.tmp_dir)

    def populate(self, conf: ComponentConfig, node_types=[et.EN_JUNCTION]):
        for i in range(1, et.ENgetcount(et.EN_NODECOUNT)[1]+1):
            # if et.ENgetnodetype(i)[1] in node_types:
            self.nodes.append(Node(i))
            # et.ENsetnodevalue(i, et.EN_EMITTER, 0)

        for i in range(1, et.ENgetcount(et.EN_LINKCOUNT)[1]+1):
            link_type = et.ENgetlinktype(i)[1]
            if link_type in [et.EN_PIPE, et.EN_CVPIPE]:
                rough = et.ENgetlinkvalue(i, et.EN_ROUGHNESS)[1]
                if rough > 140:
                    self.pipes.append(
                        Pipe(i, self.timestep, LinkType('iron'), self.nodes))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("iron", i))
                else:
                    self.pipes.append(
                        Pipe(i, self.timestep, LinkType('pvc'), self.nodes))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("pvc", i))
                self.pipes[-1].status = Status(conf.repair_vals("pipe"))
            elif link_type == et.EN_PUMP:
                self.pumps.append(
                    Pump(i, self.timestep, LinkType('pump'), self.nodes))
                self.pumps[-1].exp_elec = Exposure(*conf.exp_vals("elec", i))
                self.pumps[-1].exp_motor = Exposure(*conf.exp_vals("motor", i))
                self.pumps[-1].status_elec = Status(conf.repair_vals("elec"))
                self.pumps[-1].status_motor = Status(conf.repair_vals("motor"))

    def run(self, failures=True, pressure=True, sql_yr_w=1):
        et.ENopenH()
        et.ENinitH(0)

        # Run for two days to create network equilibrium
        time = et.ENrunH()[1]
        while time < 172800:
            et.ENnextH()[1]
            time = et.ENrunH()[1]

        while True:
            if not self.iterate(failure_sql=failures, pressure_sql=pressure, sql_yr_w=sql_yr_w):
                et.ENcloseH()
                et.ENclose()
                return

    def iterate(self, failure_sql, pressure_sql, sql_yr_w):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            for node_ in self.nodes:
                node_.save_pressure(self.current_time)
            if time % (self.year * sql_yr_w) == 0:
                print("Year done")
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
        self.db_handle.insert(tmp_pres, 'pressure',
                              '(node_id, pressure, time)')

    def failures_to_sql(self):
        tmp_lnk = list()
        for link_ in (self.pipes+self.pumps):
            tmp_lnk.extend(link_.failure)
            link_.failure.clear()
        self.db_handle.insert(tmp_lnk, 'failure', '(link_id, time, type)')