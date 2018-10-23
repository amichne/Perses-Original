from typing import List, Dict
from enum import Enum
from random import random

from component_props import Status, Exposure
# from epanet import et
from epanettools import epanet2 as et


class NodeType(Enum):
    JUNCTION = 0
    RESERVOIR = 1
    TANK = 2


class Node:
    id_ = ''
    index = None
    type_ = NodeType
    emit_coeff = 0.0
    pressure = list()

    def __init__(self, index: int):
        self.index = index
        self.get_id()
        self.get_type()

    def get_id(self):
        self.id_ = et.ENgetnodeid(self.index)[1]

    def get_type(self):
        # TODO: Pass as parameter
        self.type_ = NodeType(et.ENgetnodetype(self.index)[1])

    def get_pressure(self) -> float:
        return float(et.ENgetnodevalue(self.index, et.EN_PRESSURE)[1])

    def get_head(self) -> float:
        return float(et.ENgetnodevalue(self.index, et.EN_HEAD))

    def save_pressure(self):
        self.pressure.append(self.get_pressure())


class Link:
    id_ = ''
    index = None
    timestep = None

    from_node = Node
    to_node = Node
    outage = list()
    failures = list()

    def __init__(self, index, timestep):
        self.index = index
        self.timestep = timestep

    def get_id(self):
        self.id_ = et.ENgetlinkid(self.index)

    def get_endpoints(self):
        link_nodes = et.ENgetlinknodes(self.index)[1::]
        self.from_node = Node(link_nodes[0])
        self.to_node = Node(link_nodes[1])

    def progression(self, exp, status, temp, simtime):
        if status.functional:
            exp, status = self.inc_exposure(exp, status, temp, simtime)
        else:
            self.outage.append(simtime)
            status = status.repair(self.timestep, self.index)
        return exp, status

    def inc_exposure(self, exp, status, temp, simtime):
        if exp.failure(temp, self.timestep):
            self.failures.append(simtime)
            return exp, status
        return exp, status


class Pump(Link):
    status_elec = Status
    status_motor = Status
    exp_elec = Exposure
    exp_motor = Exposure

    def __init__(self, index):
        self.index = index
        self.get_id()
        self.get_endpoints()

    def bimodal_eval(self, temp, simtime):
        exp_l = [self.exp_elec, self.exp_motor]
        stat_l = [self.status_elec, self.status_motor]
        for i in range(0, 2):
            exp_l[i], stat_l[i] = self.progression(
                exp_l[i], stat_l[i], temp, simtime)


class Pipe(Link):
    status = Status
    exp = Exposure

    check_valve = False

    def eval(self, temp, simtime: int):
        args = [self.exp, self.status, temp, simtime]
        self.exp, self.status = self.progression(*args)
