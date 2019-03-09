from getpass import getpass

from hydraulic_simulation.multithread_controller import StatisticalMTController
from hydraulic_simulation.data_util import ComponentConfig, TasMaxProfile
from hydraulic_simulation.db_util import DatabaseHandle
from data_analysis.controller import Analytics

pass__ = getpass()
params = {'user': 'root', 'db': 'mysql',
          'host': 'localhost', 'password': pass__}


temps_to_eval = [('historical', 'data/temperature/hist_2100.txt'),
                 ('45_min', 'data/temperature/2017_2099_rcp_4.5_min.csv'),
                 ('85_min', 'data/temperature/2017_2099_rcp_8.5_min.csv'),
                 ('45_avg', 'data/temperature/2017_2099_rcp_4.5_avg.csv'),
                 ('85_avg', 'data/temperature/2017_2099_rcp_8.5_avg.csv'),
                 ('45_max', 'data/temperature/2017_2099_rcp_4.5_max.csv'),
                 ('85_max', 'data/temperature/2017_2099_rcp_8.5_max.csv')]

mid = ComponentConfig("data/current_cdf/mid_case_electronics.txt", "data/current_cdf/mid_case_motor.txt",
                      "data/current_cdf/mid_case_iron.txt", "data/current_cdf/mid_case_pvc.txt")
mid.gen_multirun_gfs(comps=65000)


for cdf_tag, comps in cdfs_to_eval:
    for temp_tag, temp_file in temps_to_eval:
        for rep_tag, rep_time in rep_to_eval:
            tasmax = TasMaxProfile(temp_file)

            with StatisticalMTController(70, tasmax, timestep=60*60*24, years=148) as example:
                params['db'] = '{0}_{1}_{2}'.format(temp_tag, cdf_tag, rep_tag)
                db = DatabaseHandle(**params)
                example.populate(comps, 112, 30750, 30750, **rep_time)
                example.create_db(db)
                example.run(failures=True, sql_yr_w=5)
                db.create_index('failure', 'links', ('link_id',))

            analysis = Analytics(params['db'], params['password'])
            analysis.run()
            analysis.clean()

            del example
            del tasmax
