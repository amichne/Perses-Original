from typing import List

from epanet import et
from components import Pump, Pipe
from component_props import Exposure, Status
from data_util import CumulativeDistFailure, TasMaxProfile, ComponentConfig


class Controller:
    # cdf_list: List[CumulativeDistFailure] = list()
    tasmax: TasMaxProfile
    pumps: List[Pump] = list()
    pipes: List[Pipe] = list()
    current_time: int = 0
    current_temp: float = 0.0
    timestep: int = 7200

    def __init__(self, network, output, tasmax):
        et.ENopen(network, output, '')
        et.ENopenH()
        et.ENinitH(0)

    def populate(self, conf: ComponentConfig):
        for i in range(1, et.ENgetcount(et.EN_LINKCOUNT)[1]+1):
            link_type = et.ENgetlinktype(i)[1]
            if link_type in [0, 1]:
                self.pipes.append(Pipe(i, self.timestep))
                # TODO: Include roughness test for PVC vs IRON
                self.pipes[-1].exp = Exposure(*conf.exp_vals("pvc"))
                self.pipes[-1].status = Status(conf.repair_vals("pipe"))
                self.pipes[-1].timestep = self.timestep
            elif link_type == 2:
                self.pumps.append(Pump(i))
                self.pumps[-1].exp_elec = Exposure(*conf.exp_vals("elec"))
                self.pumps[-1].exp_motor = Exposure(*conf.exp_vals("motor"))
                self.pumps[-1].status_elec = Status(conf.repair_time("elec"))
                self.pumps[-1].status_motor = Status(conf.repair_time("motor"))
                self.pumps[-1].timestep = self.timestep

    def run(self):
        while True:
            if not self.iterate():
                return

    def iterate(self):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            self.increment_population()

        if et.ENnextH()[1] <= 0:
            return False
        return True

    def increment_population(self):
        for pump_ in self.pumps:
            pump_.bimodal_eval(self.current_temp, self.current_time)
        for pipe_ in self.pipes:
            pipe_.eval(self.current_temp, self.current_time)
