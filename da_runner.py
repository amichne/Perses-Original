from getpass import getpass
from pprint import pprint

from data_analysis.failure_analysis import Components, ComponentFailureAnalysis
from data_analysis.pressure_analysis import NodalPressureAnalysis
from data_analysis.db_util import DatabaseHandle
from data_analysis.controller import Analytics


pass__ = getpass()
# pre = ['45', '85']
# post = ['min', 'avg', 'max']

# pre = ['45', '85']
# post = ['avg']
# params = {'user': 'root', 'password': pass__,
#           'db': None, 'host': 'localhost'}

# # for i in pre:
# #     for j in post:
# sim = 'historical_best_slow'
# params['db'] = 'historical_best_slow'
# example = ComponentFailureAnalysis(params, 'historical_best_slow')
# for comp in Components:
#     print(comp.to_str())
#     example.write_failure(comp.to_str(), sim)

# nodal = NodalPressureAnalysis(DatabaseHandle(
#     **params), 'historical_best_slow')
# th_ = 20
# annual = nodal.outages(threshold=th_, offset=43800, years=149)
# twenty = '{0}_{1}'.format(sim, str(th_))
# nodal.write_ann(twenty, annual)
# nodal.write_cum_ann(twenty, annual)
# th_ = 40
# annual = nodal.outages(threshold=th_, offset=45260, years=149)
# forty = '{0}_{1}'.format(sim, str(th_))
# nodal.write_ann(forty, annual)
# nodal.write_cum_ann(forty, annual)
analysis = Analytics('85_min_mid_standard', pass__)
analysis.run()