from getpass import getpass
from pprint import pprint

from failure_analysis import Components, FailureAnalysis


pass__ = getpass()
pre = ['45', '85']
post = ['min', 'avg', 'max']
for i in pre:
    for j in post:
        sim = ('{0}_{1}').format(i, j)
        params = {'user': 'root', 'db': sim,
                  'host': 'localhost', 'password': pass__}
        example = FailureAnalysis(params)
        for comp in Components:
            example.write_ann_cum_csv(sim, comp)
