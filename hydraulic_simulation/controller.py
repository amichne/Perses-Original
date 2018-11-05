from epanettools import epanet2 as et

from components import Pump, Pipe, Node, LinkType
from component_props import Exposure, Status
from data_util import CumulativeDistFailure, TasMaxProfile, ComponentConfig
from db_util import DatabaseHandle


class Controller:
    tasmax = None
    pumps = None
    pipes = None
    nodes = None
    current_time = None
    current_temp = None
    timestep = 7200
    year = 6307200
    db_handle = None

    def __init__(self, network, output, tasmax):
        et.ENopen(network, output, '')
        self.tasmax = tasmax
        self.pumps = list()
        self.pipes = list()
        self.nodes = list()
        self.current_time = 0
        self.current_temp = 0.0

    def populate(self, conf: ComponentConfig):
        for i in range(1, et.ENgetcount(et.EN_LINKCOUNT)[1]+1):
            link_type = et.ENgetlinktype(i)[1]
            if link_type in [et.EN_PIPE, et.EN_CVPIPE]:
                rough = et.ENgetlinkvalue(i, et.EN_ROUGHNESS)[1]
                if rough > 140:
                    self.pipes.append(Pipe(i, self.timestep, LinkType('iron')))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("iron", i))
                else:
                    self.pipes.append(Pipe(i, self.timestep, LinkType('pvc')))
                    self.pipes[-1].exp = Exposure(*conf.exp_vals("pvc", i))
                self.pipes[-1].status = Status(conf.repair_vals("pipe"))
            elif link_type == et.EN_PUMP:
                self.pumps.append(Pump(i, self.timestep, LinkType('pump')))
                self.pumps[-1].exp_elec = Exposure(*conf.exp_vals("elec", i))
                self.pumps[-1].exp_motor = Exposure(*conf.exp_vals("motor", i))
                self.pumps[-1].status_elec = Status(conf.repair_vals("elec"))
                self.pumps[-1].status_motor = Status(conf.repair_vals("motor"))
        for i in range(1, et.ENgetcount(et.EN_NODECOUNT)[1]+1):
            self.nodes.append(Node(i))

    def run(self, failures=True, pressure=True):
        et.ENopenH()
        et.ENinitH(0)
        while True:
            if not self.iterate(failure_sql=failures, pressure_sql=pressure):
                et.ENcloseH()
                et.ENclose()
                return

    def iterate(self, failure_sql=True, pressure_sql=True):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            for node_ in self.nodes:
                node_.save_pressure(self.current_time)
            if time % self.year == 0:
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

        print("Write complete for " + self.db_handle.db)

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
