from getpass import getpass
from collections import defaultdict
from os import makedirs
from datetime import date
from enum import Enum
from math import floor

from data_analysis.db_util import DatabaseHandle, database_loader
from hydraulic_simulation.components import LinkType, Link


class Components(Enum):
    PVC = 'pvc'
    IRON = 'iron'
    ELEC = 'elec'
    MOTOR = 'motor'
    PUMP = 'pump'

    def to_str(self):
        return self.value


class ComponentFailureAnalysis:
    db = DatabaseHandle
    sim_name = None

    def __init__(self, db_params, sim_name):
        self.sim_name = sim_name
        self.db = database_loader(db_params)

    def get_type(self, type_):
        return self.db.failure_type(type_)

    def pump_failures(self):
        elec_fails = self.get_type('elec')
        motor_fails = self.get_type('motor')
        fails = elec_fails + motor_fails
        return sorted(fails)

    def annual_failure(self, type_, years=148):
        coeff = 60 * 60 * 24 * 365
        bins = [0] * years

        if type_ is not 'pump':
            failures = self.get_type(type_)
        else:
            failures = self.pump_failures()

        for fail in failures:
            bins[floor(fail / coeff)] += 1
        return bins

    def cum_failure(self, type_, years=148):
        annual_bins = self.annual_failure(type_, years=years)
        cum_bins = [sum(annual_bins[0:i]) for i in range(years)]
        return cum_bins

    def write_csv(self, filepath, data):
        with open(filepath, 'w+') as handle:
            for value in data:
                handle.write(str(value) + '\n')

    def write_failure(self, component, base_dir, years=148):
        fmt = [base_dir, self.sim_name, component]
        fp = '{}/{}/failure/{}'.format(*fmt)
        fp_1 = fp + '_annual_failure.csv'
        fp_2 = fp + '_cumulative_failure.csv'
        self.write_csv(fp_1, self.annual_failure(component, years=years))
        self.write_csv(fp_2, self.cum_failure(component, years=years))


class FailureAnalysisMemory:
    sim_name = None
    pumps = None
    pvc = None
    iron = None

    def __init__(self, sim_name, pipes, pumps):
        self.sim_name = sim_name
        self.pumps = list()
        self.pvc = list()
        self.iron = list()

        for pipe in pipes:
            if pipe.type_ is LinkType('iron'):
                self.iron.extend([fail[1] for fail in pipe.failure])
            if pipe.type_ is LinkType('pvc'):
                self.pvc.extend([fail[1] for fail in pipe.failure])

        for pump in pumps:
            self.pumps.extend(pump.failure)

    def annual_failure(self, data, years=149):
        coeff = 60 * 60 * 24 * 365
        bins = [0] * years

        for component in data:
            for failure in component.failure:
                bins[floor(failure / coeff)] += 1
        return bins

    def cum_failure(self, data, years=149):
        annual_bins = self.annual_failure(data, years=years)
        cum_bins = [sum(annual_bins[0:i]) for i in range(years)]
        return cum_bins

    def write_csv(self, filepath, data):
        with open(filepath, 'w+') as handle:
            for value in data:
                handle.write(str(value) + '\n')

    def write_failure(self, component, data, base_dir, years=148):
        fmt = [base_dir, self.sim_name, component]
        fp = '{}/{}/failure/{}'.format(*fmt)
        fp_1 = fp + '_annual_failure.csv'
        fp_2 = fp + '_cumulative_failure.csv'
        self.write_csv(fp_1, self.annual_failure(data, years=years))
        self.write_csv(fp_2, self.cum_failure(data, years=years))

    def write_all(self, base_dir, years=148):
        base_dir += date.today().strftime('%Y%m%d')
        dir_ = '{}/{}/failure'.format(base_dir, self.sim_name)
        makedirs(dir_, exist_ok=True)
        for component in [('pump', self.pumps),
                          ('pvc', self.pvc),
                          ('iron', self.iron)]:
            self.write_failure(component[0],
                               component[1],
                               base_dir,
                               years=years)
