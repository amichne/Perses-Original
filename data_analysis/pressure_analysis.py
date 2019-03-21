from math import floor
from datetime import date
from os import makedirs

from data_analysis.db_util import DatabaseHandle, database_loader
from collections import defaultdict

YRSEC = 60 * 60 * 24 * 365


class NodalPressureAnalysis:
    db = None
    sim_name = None
    nodes = list()

    def __init__(self, db_params, sim_name):
        self.sim_name = sim_name
        self.db = database_loader(db_params)
        self.nodes = self.db.get_nodes()

    def outages(self, threshold, offset, years=148):
        '''Calculates the number of outages per year, for the given DB and threshold'''
        sub_list = self.db.outage_by_time(threshold)
        annual_ct = [0] * (years + 1)
        for sub in sub_list:
            try:
                annual_ct[floor(sub[1] / YRSEC)] += 1
            except IndexError:
                print('Pressure analysis outages error')
                print('{0} '.format(len(ct)) for ct in annual_ct)
                print(sub)
                print(sub[1] % YRSEC)
                exit()
        for index in range(years):
            annual_ct[index] = annual_ct[index] - offset
            if annual_ct[index] < 0:
                annual_ct[index] = 0
        return annual_ct

    def outages_mem(self, outages, offset, years=148):
        pass

    def write_ann(self, data, threshold, base_dir='output'):
        fmt = [base_dir, self.sim_name, str(threshold)]
        fp = '{}/{}/pressure/sub_{}'.format(*fmt)
        fp = fp + 'psi_annual_pressure_outage.csv'
        with open(fp, 'w+') as handle:
            handle.write('\n'.join([str(yr) for yr in data]))

    def write_cum_ann(self, data, threshold, base_dir='output'):
        fmt = [base_dir, self.sim_name, str(threshold)]
        fp = '{}/{}/pressure/sub_{}'.format(*fmt)
        fp = fp + 'psi_cumulative_annual_pressure_outage.csv'
        with open(fp, 'w+') as handle:
            handle.write('\n'.join([str(sum(data[0:i]))
                                    for i in range(len(data))]))


class PressureAnalysisMemory:
    sim_name = None
    nodes = list()

    def __init__(self, sim_name, nodes):
        self.sim_name = sim_name
        self.nodes = nodes

    def outages(self, threshold, offset, years=148):
        '''Calculates the number of outages per year, for the given DB and threshold'''
        # TODO
        annual_ct = [0] * (years + 1)
        for node in self.nodes:
            for year, count in enumerate(node.threshold[threshold]):
                annual_ct[year] += count
        for year in range(years):
            annual_ct[year] -= offset
            if annual_ct[year] < 0:
                annual_ct[year] = 0
        return annual_ct

    def cum_outages(self, threshold, offset, years=148):
        annual_bins = self.outages(threshold, offset, years=years)
        cum_bins = [sum(annual_bins[0:i]) for i in range(years)]
        return cum_bins

    def write_csv(self, filepath, data):
        with open(filepath, 'w+') as handle:
            for value in data:
                handle.write(str(value) + '\n')

    def write_failure(self, threshold, offset, base_dir, years=148):
        base_dir += date.today().strftime('%Y%m%d')
        fmt = [base_dir, self.sim_name, threshold]
        dir_ = '{}/{}/pressure'.format(base_dir, self.sim_name)
        makedirs(dir_, exist_ok=True)
        fp = '{}/{}/pressure/sub_{}'.format(*fmt)
        fp_1 = fp + 'psi_annual_pressure.csv'
        fp_2 = fp + 'psi_cumulative_pressure.csv'
        self.write_csv(fp_1, self.outages(threshold, offset, years=years))
        self.write_csv(fp_2, self.cum_outages(threshold, offset, years=years))
