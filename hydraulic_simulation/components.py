from typing import List, Dict
from math import isnan, floor
from enum import Enum
from random import random, choice

from hydraulic_simulation.component_props import Status, Exposure
# from epanet import et
from epanettools import epanet2 as et
YRSEC = 60 * 60 * 24 * 365


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
    threshold = dict()
    run_epa = True

    # def __init__(self, index: int, years, pressure_low_th, pressure_high_th):
    def __init__(self, index: int):
        self.index = index
        self.get_id()
        self.get_type()
        # self.pressure_low_th = pressure_low_th
        # self.pressure_high_th = pressure_high_th
        # self.threshold = {pressure_low_th: [0]*years,
        #                 pressure_high_th: [0]*years}

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

    def save_pressure(self, timestep):
        self.pressure.append([self.id_, self.get_pressure(), timestep])

    # def get_threshold(self):
    #     tmp = float(et.ENgetnodevalue(self.index, et.EN_PRESSURE)[1])
    #     if not isnan(tmp):
    #         if tmp < self.pressure_high_th:
    #             if tmp < self.pressure_low_th:
    #                 return (True, True)
    #         return (False, True)
    #     return (False, False)

    # def save_threshold(self, current_time):
    #     tmp = self.get_threshold()
    #     year = floor(current_time / YRSEC)
    #     if tmp[0]:
    #         self.threshold[self.pressure_low_th][year] += 1
    #     if tmp[1]:
    #         self.threshold[self.pressure_high_th][year] += 1


class Link:
    id_ = ''
    run_epa = False
    type_ = LinkType
    index = None
    timestep = None

    outage = None
    failure = None

    def __init__(self, index, timestep, type_, run_epa=True):
        self.run_epa = run_epa
        self.index = index
        self.timestep = timestep
        self.type_ = LinkType(type_)
        self.failure = list()
        self.outage = list()

        if self.run_epa:
            self.id_ = et.ENgetlinkid(self.index)[1]

    def progression(self, exp, status, temp, simtime, type_):
        if status.functional:
            exp, status = self.inc_exposure(
                exp, status, temp, simtime, type_)
        else:
            self.outage.append([self.id_, simtime, type_.value])
            status = status.repair(self.index, self.timestep, self.run_epa)
        return exp, status

    def inc_exposure(self, exp, status, temp, simtime, type_):
        if exp.failure(temp, self.timestep):
            self.failure.append([self.id_, simtime, type_.value])
            status.disable(index=self.index, epa=self.run_epa)
            return exp, status
        return exp, status


class Pump(Link):
    status_elec = None
    status_motor = None
    exp_elec = None
    exp_motor = None

    def bimodal_eval(self, temp, simtime):
        self.exp_elec, self.status_elec = self.progression(
            self.exp_elec, self.status_elec, temp, simtime, LinkType('elec'))
        self.exp_motor, self.status_motor = self.progression(
            self.exp_motor, self.status_motor, temp, simtime, LinkType('motor'))


class Pipe(Link):
    status = None
    exp = None
    check_valve = False

    def eval(self, temp, simtime):
        '''
        Evaluate exposure progression for TAS Max and Simtime:
            temp: float of tasmax in deg C
            simtime: int for current time of simulation in seconds'''
        self.exp, self.status = self.progression(
            self.exp, self.status, temp, simtime, self.type_)
