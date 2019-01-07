from getpass import getpass
from epanettools import epanet2 as et

from controller import Controller
from data_util import ComponentConfig, TasMaxProfile
from db_util import DatabaseHandle

pass__ = getpass()
params = {'user': 'root', 'db': 'example',
          'host': 'localhost', 'password': pass__}

net_file = "data/north_marin_c.inp"
output_file = "output/output_nmc.rpt"

# temps_to_eval = {'45_min': 'data/temperature/2017_2099_rcp_4.5_min.csv',
#                  '85_min': 'data/temperature/2017_2099_rcp_8.5_min.csv',
#                  '45_avg': 'data/temperature/2017_2099_rcp_4.5_avg.csv',
#                  '85_avg': 'data/temperature/2017_2099_rcp_8.5_avg.csv',
#                  '45_max': 'data/temperature/2017_2099_rcp_4.5_max.csv',
#                  '85_max': 'data/temperature/2017_2099_rcp_8.5_max.csv'}

temps_to_eval = {'45_avg': 'data/temperature/2017_2099_rcp_4.5_avg.csv',
                 '85_avg': 'data/temperature/2017_2099_rcp_8.5_avg.csv'}

comps = ComponentConfig("data/current_cdf/mid_case_electronics.txt", "data/current_cdf/mid_case_motor.txt",
                        "data/current_cdf/mid_case_iron.txt", "data/current_cdf/mid_case_pvc.txt")
comps.gen_multirun_gfs()

for db_name, temp_file in list(temps_to_eval.items()):
    tasmax = TasMaxProfile(temp_file)

    with Controller(net_file, output_file, tasmax) as example:
        params['db'] = db_name
        db = DatabaseHandle(**params)
        example.populate(comps)
        example.create_db(db)

        example.run(sql_yr_w=5)
        db.create_index('failure', 'links', ('link_id',))
        db.create_index('pressure', 'nodes', ('node_id',))
        db.create_index('pressure', 'subs', ('node_id', 'pressure', ))

    del example
    del tasmax
