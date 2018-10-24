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
        return float(et.ENgetnodevalue(self.index, et.EN_HEAD)[1])

    def save_pressure(self, timestep):
        self.pressure.append((self.id_, self.get_pressure(), timestep))


class Link:
    id_ = ''
    type_ = LinkType
    index = None
    timestep = None

    from_node = Node
    to_node = Node
    outage = None
    failure = None

    def __init__(self, index, timestep, type_):
        self.index = index
        self.timestep = timestep
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
            status = status.repair(self.index, self.timestep)
        return exp, status

    def inc_exposure(self, exp, status, temp, simtime, type_):
        if exp.failure(temp, self.timestep):
            self.failure.append((self.id_, simtime, type_.value))
            print(type_.value, self.id_, ": ", str(len(self.failure)))
            status.disable(self.index)
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
