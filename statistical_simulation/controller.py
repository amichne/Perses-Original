import numpy as np
import pandas as pd

from statistical_simulation.components import ComponentPopulation

YEAR = 60 * 60 * 24 * 365


class StatisticalController:
    name = None
    timestep = None
    current_time = None
    current_temp = None
    tasmax = None

    motor = None
    elec = None
    iron = None
    pvc = None

    def __init__(self, name, tasmax, years=82, timestep=60*60):
        print("initializing")
        self.name = name
        self.time = ((48 * 60 * 60) + (years * YEAR))
        self.timestep = timestep
        self.current_time = 0
        self.current_temp = 0.0
        self.tasmax = tasmax

    def populate(self, motor, elec, iron, pvc):
        print("populating")
        self.motor = ComponentPopulation(motor.name, motor.n, motor.cdf)
        self.motor.populate(motor.repair_time, gf=motor.gf)

        self.elec = ComponentPopulation(elec.name, elec.n, elec.cdf)
        self.elec.populate(elec.repair_time, gf=elec.gf)

        self.iron = ComponentPopulation(iron.name, iron.n, iron.cdf)
        self.iron.populate(iron.repair_time, gf=iron.gf)

        self.pvc = ComponentPopulation(pvc.name, pvc.n, pvc.cdf)
        self.pvc.populate(pvc.repair_time, gf=pvc.gf)

    def run(self, directory='output'):
        print('iterating')
        while self.current_time < self.time:
            self.current_time += self.timestep
            self.iterate()
        print("writing failure")
        components = [
            self.motor,
            self.elec,
            self.iron,
            self.pvc
        ]
        for component in components:
            component.write_failure(
                f'{self.name}_{component.name}_failure.txt', directory + '/')

    def iterate(self):
        self.current_temp =\
            float(self.tasmax.data.iat[int(self.current_time / 86400)])
        components = [self.motor,
                      self.elec,
                      self.iron,
                      self.pvc]
        for component in components:
            component.increment_njit(self.current_temp,
                                     self.timestep,
                                     self.current_time)
