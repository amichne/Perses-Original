from shutil import rmtree
from os import makedirs

from epanettools import epanet2 as et
from hydraulic_simulation.data_util import CumulativeDistFailure,\
    TasMaxProfile, ComponentConfig, RepairPeriods
from hydraulic_simulation.controller import Controller
from hydraulic_simulation.data_util import ComponentConfig
from hydraulic_simulation.components import Pump, Pipe, Node, LinkType
from hydraulic_simulation.component_props import Exposure, Status


class EpaNETController(Controller):

    db_handle = None

    def __init__(self, network, output, tasmax, years=82, timestep=60*60, tmp_dir='data/tmp/'):
        # super().__init__(output, tasmax, years=years, timestep=timestep, tmp_dir=tmp_dir)
        self.tmp_dir = tmp_dir
        self.tasmax = tasmax
        self.pumps = list()
        self.pipes = list()
        self.nodes = list()
        self.current_time = 0
        self.current_temp = 0.0
        self.timestep = timestep
        self.time = ((48 * 60 * 60) + (years * self.year))
        self.years = years

        rmtree(self.tmp_dir, ignore_errors=True)
        makedirs(tmp_dir)
        et.ENopen(network, output, '')
        et.ENsettimeparam(0, self.time)
        network = tmp_dir + network.split('/')[-1]
        output = tmp_dir + output.split('/')[-1]
        et.ENsaveinpfile(network)
        et.ENclose()
        et.ENopen(network, output, '')
        self.network = network

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        rmtree(self.tmp_dir)

    def populate(self, conf: ComponentConfig, node_types=[et.EN_JUNCTION], thresholds=(20, 40), motor_repair=25200, elec_repair=14400, pipe_repair=316800):
        for i in range(1, et.ENgetcount(et.EN_NODECOUNT)[1]+1):
            self.nodes.append(Node(i))
            # self.nodes.append(Node(i,
            #                        self.years,
            #                        thresholds[0],
            #                        thresholds[1]))

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

    def run(self, pressure=True, failure=True, sql_yr_w=5):
        et.ENopenH()
        et.ENinitH(0)

        # Run for two days to create network equilibrium
        time = et.ENrunH()[1]
        while time < 172800:
            et.ENnextH()[1]
            time = et.ENrunH()[1]

        while True:
            if not self.iterate(pressure, failure, sql_yr_w=sql_yr_w):
                et.ENcloseH()
                et.ENclose()
                return

    def iterate(self, pressure, failure, sql_yr_w):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            for node_ in self.nodes:
                node_.save_pressure(self.current_time)
            if (time % (self.year * sql_yr_w)) == 0:
                print("{} year(s) done".format(str(time / self.year)))
                if pressure:
                    self.pressure_to_sql()
                if failure:
                    self.failures_to_sql()
            self.increment_population()
        if et.ENnextH()[1] <= 0:
            print("Simulation Complete.")
            return False
        return True

    def increment_population(self):
        for pump in self.pumps:
            pump.bimodal_eval(self.current_temp, self.current_time)
        for pipe in self.pipes:
            pipe.eval(self.current_temp, self.current_time)
