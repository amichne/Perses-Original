from getpass import getpass
from epanettools import epanet2 as et
from collections import OrderedDict

from hydraulic_simulation.controller import Controller
from hydraulic_simulation.data_util import ComponentConfig, TasMaxProfile
from hydraulic_simulation.db_util import DatabaseHandle
from data_analysis.controller import Analytics

pass__ = getpass()
params = {'user': 'root', 'db': 'example',
          'host': 'localhost', 'password': pass__}

net_file = "data/north_marin_c.inp"
output_file = "data/output_nmc.rpt"
bin_file = "data/output_nmc.bin"

# temps_to_eval = {'45_avg': 'data/temperature/2017_2099_rcp_4.5_avg.csv',
#                  '85_avg': 'data/temperature/2017_2099_rcp_8.5_avg.csv'}


temps_to_eval = [('historical', 'data/temperature/hist_2100.txt'),
                 ('45_min', 'data/temperature/2017_2099_rcp_4.5_min.csv'),
                 ('85_min', 'data/temperature/2017_2099_rcp_8.5_min.csv'),
                 ('45_avg', 'data/temperature/2017_2099_rcp_4.5_avg.csv'),
                 ('85_avg', 'data/temperature/2017_2099_rcp_8.5_avg.csv'),
                 ('45_max', 'data/temperature/2017_2099_rcp_4.5_max.csv'),
                 ('85_max', 'data/temperature/2017_2099_rcp_8.5_max.csv')]

# temps_to_eval = {'45_min': 'data/temperature/2017_2099_rcp_4.5_min.csv',
#                  '85_min': 'data/temperature/2017_2099_rcp_8.5_min.csv',
#                  '45_avg': 'data/temperature/2017_2099_rcp_4.5_avg.csv',
#                  '85_avg': 'data/temperature/2017_2099_rcp_8.5_avg.csv',
#                  '45_max': 'data/temperature/2017_2099_rcp_4.5_max.csv',
#                  '85_max': 'data/temperature/2017_2099_rcp_8.5_max.csv'}

best = ComponentConfig("data/current_cdf/best_case_electronics.txt", "data/current_cdf/best_case_motor.txt",
                       "data/current_cdf/best_case_iron.txt", "data/current_cdf/best_case_pvc.txt")
mid = ComponentConfig("data/current_cdf/mid_case_electronics.txt", "data/current_cdf/mid_case_motor.txt",
                      "data/current_cdf/mid_case_iron.txt", "data/current_cdf/mid_case_pvc.txt")
worst = ComponentConfig("data/current_cdf/worst_case_electronics.txt", "data/current_cdf/worst_case_motor.txt",
                        "data/current_cdf/worst_case_iron.txt", "data/current_cdf/worst_case_pvc.txt")
best.gen_multirun_gfs()
mid.gen_multirun_gfs()
worst.gen_multirun_gfs()

cdfs_to_eval = [('best', best), ('mid', mid), ('worst', worst)]
# cdfs_to_eval = [('mid', mid)]

rep_to_eval = [('slow', {'motor_repair': 25200*2, 'elec_repair': 14400*2, 'pipe_repair': 316800*2}),
               ('standard', {'motor_repair': 25200,
                             'elec_repair': 14400, 'pipe_repair': 316800}),
               ('fast', {'motor_repair': 25200*.5, 'elec_repair': 14400*.5, 'pipe_repair': 316800*.5})]
# rep_to_eval = [
#     ('standard', {'motor_repair': 25200,
#                   'elec_repair': 14400, 'pipe_repair': 316800})
# ]

for cdf_tag, comps in cdfs_to_eval:
    for temp_tag, temp_file in temps_to_eval:
        for rep_tag, rep_time in rep_to_eval:
            tasmax = TasMaxProfile(temp_file)

            with Controller(net_file, output_file, tasmax, years=148) as example:
                params['db'] = '{0}_{1}_{2}'.format(temp_tag, cdf_tag, rep_tag)
                db = DatabaseHandle(**params)
                example.populate_epa(comps, **rep_time)
                example.create_db(db)

                example.run(failures=True, pressure=True, sql_yr_w=10)
                db.create_index('failure', 'links', ('link_id',))
                db.create_index('pressure', 'nodes', ('node_id',))
                db.create_index('pressure', 'subs', ('node_id', 'pressure', ))

            analysis = Analytics(params['db'], params['password'])
            analysis.run()
            analysis.clean()

            del example
            del tasmax