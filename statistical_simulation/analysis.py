from getpass import getpass
from collections import defaultdict
from enum import Enum
from math import floor


class StatisticalFailureAnalysis:
    sim_name = None

    def __init__(self, sim_name):
        self.sim_name = sim_name

    def annual(self, filename, component, years=148):
        coeff = 60 * 60 * 24 * 365
        bins = [0] * (years + 1)

        with open(filename, 'r') as handle:
            failures = handle.read().splitlines()

        for failure in failures:
            bins[floor(int(failure.split(',')[2].strip()) / coeff)] += 1
        return bins

    def cumulative(self, filename, component, years=148):
        bins = self.annual(filename, component, years=years)
        return [sum(bins[0:i]) for i in range(years+1)]

    def failure(self, component, base_dir, years):
        fp = f'{base_dir}/{self.sim_name}_{component}'
        fp_1 = fp + '_annual_failure.csv'
        fp_2 = fp + '_cumulative_failure.csv'
        filename = f'{base_dir}/{self.sim_name}_{component}_failure.txt'
        print(f'--- {fp_1} ---\n--- {fp_2} ---\n--- {filename} ---')
        self.write_csv(fp_1,
                       self.annual(filename,
                                   component,
                                   years=years))
        self.write_csv(fp_2,
                       self.cumulative(filename,
                                       component,
                                       years=years))

    def write_csv(self, filepath, data):
        with open(filepath, 'w+') as handle:
            for value in data:
                handle.write(str(value) + '\n')


if __name__ == '__main__':
    name = 'historical_mid_standard_20190309'
    base_dir = f'output/statistical_20190309'
    analysis = StatisticalFailureAnalysis(name)
    for component in ['motor', 'elec', 'iron', 'pvc']:
        analysis.failure(component,
                         base_dir,
                         years=35)
