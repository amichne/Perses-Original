from getpass import getpass
from pprint import pprint

from failure_analysis import Components, ComponentFailureAnalysis
from pressure_analysis import NodalPressureFailure
from db_util import DatabaseHandle


pass__ = getpass()
# pre = ['45', '85']
# post = ['min', 'avg', 'max']

pre = ['45', '85']
post = ['avg']
params = {'user': 'root', 'password': pass__,
          'db': None, 'host': 'localhost'}

for i in pre:
    for j in post:
        sim = ('{0}_{1}').format(i, j)
        params['db'] = sim
        example = ComponentFailureAnalysis(params)
        for comp in Components:
            example.write_ann_cum_csv(sim, comp)

        nodal = NodalPressureFailure(DatabaseHandle(**params))
        annual = nodal.annual_outages()
        nodal.write_ann(sim, annual)
