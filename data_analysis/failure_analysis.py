from getpass import getpass
from collections import defaultdict
from enum import Enum
from math import floor

from db_util import DatabaseHandle


class Components(Enum):
    PVC = 'pvc'
    IRON = 'iron'
    ELEC = 'elec'
    MOTOR = 'motor'
    PUMP = 'pump'

    def to_str(self):
        pass


class FailureAnalysis:
    db = DatabaseHandle

    def __init__(self, db_params):
        self.db = DatabaseHandle(**db_params)

    def get_type(self, type_):
        return self.db.failure_type(type_)

    def pump_failures(self):
        elec_fails = self.get_type(Components.ELEC)
        motor_fails = self.get_type(Components.MOTOR)
        fails = elec_fails + motor_fails
        return sorted(fails)

    def annual_failure(self, type_, years=82):
        coeff = 60 * 60 * 24 * 365
        bins = [0] * years

        if type_ is not Components.PUMP:
            failures = self.get_type(type_)
        else:
            failures = self.pump_failures()

        for fail in failures:
            bins[floor(fail / coeff)] += 1
        return bins

    def cum_failure(self, type_, years=82):
        annual_bins = self.annual_failure(type_, years=years)
        cum_bins = [sum(annual_bins[0:i]) for i in range(years)]
        return cum_bins

    def write_csv(self, filepath, data):
        with open(filepath, 'w+') as handle:
            for value in data:
                handle.write(str(value) + '\n')

    def write_ann_cum_csv(self, sim_name, type_, years=82):
        pre = ('{0}_{1}').format(sim_name, type_.value)
        fp_1 = ('../output/{0}_annual_fail.csv').format(pre)
        fp_2 = ('../output/{0}_cumulative_fail.csv').format(pre)
        self.write_csv(fp_1, self.annual_failure(type_, years=years))
        self.write_csv(fp_2, self.cum_failure(type_, years=years))
