from db_util import DatabaseHandle
from collections import defaultdict

YRSEC = 60 * 60 * 24 * 365


class NodalPressureFailure:
    db = None
    nodes = list()
    sub_20 = dict()
    sub_40 = dict()

    def __init__(self, db_handle):
        self.db = db_handle
        self.nodes = self.db.get_nodes()

    def get_outage_ct(self):
        for node in self.nodes:
            self.sub_20[node] = self.db.get_ct_sub_thresh(node, 20)
            self.sub_40[node] = self.db.get_ct_sub_thresh(node, 40)
        return (self.sub_20, self.sub_40)

    def annual_outages(self, threshold=20, years=82):
        sub_list = self.db.get_outages_by_time(threshold)
        annual_ct = [0] * years
        for sub in sub_list:
            annual_ct[sub[1] % YRSEC] += 1
        return annual_ct

    def write_ann(self, file_header, data):
        with open(file_header + "_annual_failure.csv", 'w+') as handle:
            handle.write(str(yr) + '\n' for yr in data)

    # def write_cum_ann
