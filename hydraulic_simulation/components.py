from typing import List, Dict
from math import isnan
from enum import Enum
from random import random, choice

from component_props import Status, Exposure
# from epanet import et
from epanettools import epanet2 as et


class NodeType(Enum):
    JUNCTION = 0
    RESERVOIR = 1
    TANK = 2


class LinkType(Enum):
    PVC = 'pvc'
    IRON = 'iron'
    PUMP = 'pump'
    ELEC = 'elec'
    MOTOR = 'motor'


class Node:
    id_ = None
    index = None
    type_ = NodeType
    emit_coeff = 0.0
    pressure = list()

    def __init__(self, index: int, run_init=True):
        self.index = index
        if run_init:
            self.get_id()
            self.get_type()

    def get_id(self):
        self.id_ = et.ENgetnodeid(self.index)[1]

    def get_type(self):
        # TODO: Pass as parameter
        self.type_ = NodeType(et.ENgetnodetype(self.index)[1])

    def get_pressure(self) -> float:
        tmp = float(et.ENgetnodevalue(self.index, et.EN_PRESSURE)[1])
        if not isnan(tmp):
            return tmp
        else:
            print("Index: ", self.index, ", ID: ", self.id_)
            input()
            return 0.0

    def get_head(self) -> float:
        return float(et.ENgetnodevalue(self.index, et.EN_HEAD)[1])

    def save_pressure(self, timestep):
        self.pressure.append((self.id_, self.get_pressure(), timestep))


class Link:
    id_ = ''
    type_ = LinkType
    index = None
    timestep = None
    demand_nodes = None

    from_node = Node
    to_node = Node
    emitter_node = None
    outage = None
    failure = None

    def __init__(self, index, timestep, type_, demand_nodes):
        self.index = index
        self.timestep = timestep
        self.demand_nodes = demand_nodes
        self.id_ = et.ENgetlinkid(self.index)[1]
        self.type_ = LinkType(type_)
        self.failure = list()
        self.outage = list()
        self.get_endpoints()

    def get_endpoints(self):
        link_nodes = et.ENgetlinknodes(self.index)[1::]
        self.from_node = Node(link_nodes[0])
        self.to_node = Node(link_nodes[1])

    def progression(self, exp, status, temp, simtime, type_):
        if status.functional:
            exp, status = self.inc_exposure(
                exp, status, temp, simtime, type_)
        else:
            self.outage.append((self.id_, simtime, type_.value))
            status = status.repair(
                self.index, self.timestep, self.emitter_node)
        return exp, status

    def inc_exposure(self, exp, status, temp, simtime, type_):
        if exp.failure(temp, self.timestep):
            # try:
            self.emitter_node = choice([self.from_node, self.to_node])
            # except IndexError:
            #       self.emitter_node = Node(-1, run_init=False)
            print('Emitter selected: ', self.emitter_node.index)
            print(type_.value,  "failure for component: ",
                  self.id_, "at time :", simtime)
            self.failure.append((self.id_, simtime, type_.value))
            status.disable(index=self.index, node=self.emitter_node)
            return exp, status
        return exp, status


class Pump(Link):
    status_elec = Status
    status_motor = Status
    exp_elec = Exposure
    exp_motor = Exposure

    def bimodal_eval(self, temp, simtime):
        self.exp_elec, self.status_elec = self.progression(
            self.exp_elec, self.status_elec, temp, simtime, LinkType('elec'))
        self.exp_motor, self.status_motor = self.progression(
            self.exp_motor, self.status_motor, temp, simtime, LinkType('motor'))


class Pipe(Link):
    status = Status
    exp = Exposure
    check_valve = False

    def eval(self, temp, simtime):
        '''
        Evaluate exposure progression for TAS Max and Simtime:
            temp: float of tasmax in deg C
            simtime: int for current time of simulation in seconds'''
        self.exp, self.status = self.progression(
            self.exp, self.status, temp, simtime, self.type_)
