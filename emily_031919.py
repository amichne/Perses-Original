from getpass import getpass
from epanettools import epanet2 as et
from collections import OrderedDict
from itertools import product

from hydraulic_simulation.epa_controller import EpaNETController
from hydraulic_simulation.data_util import ComponentConfig, TasMaxProfile
from hydraulic_simulation.db_util import DatabaseHandle
from data_analysis.failure_analysis import FailureAnalysisMemory
from data_analysis.pressure_analysis import PressureAnalysisMemory
from hydraulic_simulation.db_util import DatabaseHandle
from data_analysis.controller import Analytics

pass__ = getpass()
params = {'user': 'root', 'db': 'example',
          'host': 'localhost', 'password': pass__}

net_file = "data/network/north_marin_c.inp"
output_file = "data/network/output_nmc.rpt"
bin_file = "data/network/output_nmc.bin"

temps = [
    ('historical', 'data/temperature/hist_2100.txt'),
    ('45_min', 'data/temperature/2017_2099_rcp_4.5_min.csv'),
    ('45_avg', 'data/temperature/2017_2099_rcp_4.5_avg.csv'),
    ('45_max', 'data/temperature/2017_2099_rcp_4.5_max.csv'),
    ('85_min', 'data/temperature/2017_2099_rcp_8.5_min.csv'),
    ('85_avg', 'data/temperature/2017_2099_rcp_8.5_avg.csv'),
    ('85_max', 'data/temperature/2017_2099_rcp_8.5_max.csv')
]


best = ComponentConfig("data/cdf/best_case_electronics.txt",
                       "data/cdf/best_case_motor.txt",
                       "data/cdf/best_case_iron.txt",
                       "data/cdf/best_case_pvc.txt")
mid = ComponentConfig("data/cdf/mid_case_electronics.txt",
                      "data/cdf/mid_case_motor.txt",
                      "data/cdf/mid_case_iron.txt",
                      "data/cdf/mid_case_pvc.txt")
worst = ComponentConfig("data/cdf/worst_case_electronics.txt",
                        "data/cdf/worst_case_motor.txt",
                        "data/cdf/worst_case_iron.txt",
                        "data/cdf/worst_case_pvc.txt")

# Generate one set of god-factors, and apply them to each of the case-types
# used in this simulation

best.gen_multirun_gfs()
mid.set_multirun_gfs(best.elec_gf, best.motor_gf, best.iron_gf, best.pvc_gf)
worst.set_multirun_gfs(best.elec_gf, best.motor_gf, best.iron_gf, best.pvc_gf)

cdfs = [('best', best), ('mid', mid), ('worst', worst)]

reps = [('slow', {'motor_repair': 25200*2,
                  'elec_repair': 14400*2,
                  'pipe_repair': 316800*2}),
        ('standard', {'motor_repair': 25200,
                      'elec_repair': 14400,
                      'pipe_repair': 316800}),
        ('fast', {'motor_repair': 25200*.5,
                  'elec_repair': 14400*.5,
                  'pipe_repair': 316800*.5})]

simulations = ((temp, cdf, rep)
               for temp in temps for cdf in cdfs for rep in reps)


thresholds = {'fail': 20, 'disfunc': 40}
offsets = {'fail': 43800, 'disfunc': 840960}
YEARS = 148

for sim in simulations:
    temp_tag, temp_file = sim[0]
    cdf_tag, comps = sim[1]
    rep_tag, rep_time = sim[2]
    tasmax = TasMaxProfile(temp_file)

    with EpaNETController(net_file, output_file, tasmax, years=YEARS, timestep=60*60) as example:
        params['db'] = '{0}_{1}_{2}'.format(temp_tag, cdf_tag, rep_tag)
        db = DatabaseHandle(**params)
        example.create_db(db)
        example.populate(comps, **rep_time)
        example.run(True, True)

        db.create_index('failure', 'links', ('link_id',))
        db.create_index('pressure', 'nodes', ('node_id',))
        db.create_index('pressure', 'subs', ('node_id', 'pressure', ))

        analysis = Analytics(params['db'], params['password'])
        analysis.run_db()
        analysis.clean()
        print('Data Analysis Complete.')
