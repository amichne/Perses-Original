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
        th_ = 20
        annual = nodal.annual_outages(threshold=th_)
        twenty = '{0}_{1}'.format(sim, str(th_))
        nodal.write_ann(twenty, annual)
        nodal.write_cum_ann(twenty, annual)
        th_ = 40
        annual = nodal.annual_outages(threshold=th_)
        forty = '{0}_{1}'.format(sim, str(th_))
        nodal.write_ann(forty, annual)
        nodal.write_cum_ann(forty, annual)
