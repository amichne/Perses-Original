from dataclasses import dataclass
from random import random
from typing import List, Tuple


@dataclass
class CumulativeDistFailure:
    ''' The CDF file exists as a text file where each
        line holds a float, representing the percent
        of the population failed at that (deg C) * Year'''
    values: List[float] = None
    component_type: str = None
    meta: str = None

    def __init__(self, filepath, type_, meta=""):
        with open(filepath, 'r') as handle:
            self.values = [float(x.strip()) for x in handle.readlines()]
        self.component_type = type_
        self.meta = meta


class TasMaxProfile:
    values: List[float] = None

    def __init__(self, filepath):
        values = open(filepath, 'r').readlines()
        self.values = [float(val[1]) for val in values]

    def temp(self, time_seconds):
        return self.values[int(time_seconds / 86400)]


class ComponentConfig:
    elec_cdf: List[float]
    motor_cdf: List[float]
    iron_cdf: List[float]
    pvc_cdf: List[float]
    elec_gf: List[float] = None
    motor_gf: List[float] = None
    iron_gf: List[float] = None
    pvc_gf: List[float] = None
    motor_repair = 158400
    elec_repair = 158400
    pipe_repair = 316800

    def __init__(self, elec_fp, motor_fp, iron_fp, pvc_fp):
        self.elec_cdf = CumulativeDistFailure(elec_fp, "Electric")
        self.motor_cdf = CumulativeDistFailure(motor_fp, "Motor")
        self.iron_cdf = CumulativeDistFailure(iron_fp, "Iron Pipe")
        self.pvc_cdf = CumulativeDistFailure(pvc_fp, "PVC Pipe")

    def exp_vals(self, component, n=100) -> Tuple[List[float], List[float]]:
        if component == "elec":
            if self.elec_gf is None:
                return (self.elec_cdf, [random() for i in range(n)])
            return [self.elec_cdf, self.elec_gf]
        if component == "motor":
            if self.motor_gf is None:
                return (self.motor_cdf, [random() for i in range(n)])
            return [self.motor_cdf, self.motor_gf]
        if component == "iron":
            if self.iron_gf is None:
                return (self.iron_cdf, [random() for i in range(n)])
            return [self.iron_cdf, self.iron_gf]
        if component == "pvc":
            if self.pvc_gf is None:
                return (self.pvc_cdf, [random() for i in range(n)])
            return [self.pvc_cdf, self.pvc_gf]
        raise ValueError("Not a valid component type")

    def repair_vals(self, component):
        if component == "elec":
            return self.elec_repair
        if component == "motor":
            return self.motor_repair
        if component == "pipe":
            return self.pipe_repair
        raise ValueError("Not a valid component type")
