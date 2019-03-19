from datetime import date
from os import mkdir
from shutil import rmtree
import time

from statistical_simulation.config import *
from statistical_simulation.components import Exposure, Status, ComponentPopulation
from statistical_simulation.controller import StatisticalController
from statistical_simulation.analysis import StatisticalFailureAnalysis

YEARS = 148
# YEARS = 35
TIMESTEP = 60*60*24


component_counts = [112, 112, 30750, 30750]
# component_counts = [5, 5, 5, 5]
# component_counts = [5, 5, 2000, 2000]

depth = [100, 100, 100, 100]
gfs = [create_gfs(component_counts[0], depth[0]),
       create_gfs(component_counts[1], depth[1]),
       create_gfs(component_counts[2], depth[2]),
       create_gfs(component_counts[3], depth[3])
       ]
mid_cdfs = [Cdf("data/current_cdf/mid_case_electronics.txt"),
            Cdf("data/current_cdf/mid_case_motor.txt"),
            Cdf("data/current_cdf/mid_case_iron.txt"),
            Cdf("data/current_cdf/mid_case_pvc.txt")]

best_cdfs = [Cdf("data/current_cdf/best_case_electronics.txt"),
             Cdf("data/current_cdf/best_case_motor.txt"),
             Cdf("data/current_cdf/best_case_iron.txt"),
             Cdf("data/current_cdf/best_case_pvc.txt")]
worst_cdfs = [Cdf("data/current_cdf/worst_case_electronics.txt"),
              Cdf("data/current_cdf/worst_case_motor.txt"),
              Cdf("data/current_cdf/worst_case_iron.txt"),
              Cdf("data/current_cdf/worst_case_pvc.txt")]


tasmax_to_eval = [('historical', Temperature('data/temperature/hist_2100.txt')),
                  ('45_min', Temperature('data/temperature/2017_2099_rcp_4.5_min.csv')),
                  ('85_min', Temperature('data/temperature/2017_2099_rcp_8.5_min.csv')),
                  ('45_avg', Temperature('data/temperature/2017_2099_rcp_4.5_avg.csv')),
                  ('85_avg', Temperature('data/temperature/2017_2099_rcp_8.5_avg.csv')),
                  ('45_max', Temperature('data/temperature/2017_2099_rcp_4.5_max.csv')),
                  ('85_max', Temperature('data/temperature/2017_2099_rcp_8.5_max.csv'))]

cdfs_to_eval = [('mid', mid_cdfs), ('best', best_cdfs), ('worst', worst_cdfs)]
rep_to_eval = [('normal', [25200, 14400, 316800, 316800]),
               ('slow', [25200, 14400, 316800, 316800]),
               ('fast', [25200, 14400, 316800, 316800])]


today = date.today().strftime('%Y%m%d')
base_dir = f'output/statistical_{today}'
rmtree(base_dir, ignore_errors=True)
mkdir(base_dir)

for rep_name, rep in rep_to_eval:
    for cdf_name, cdf in cdfs_to_eval:
        for tas_name, tas in tasmax_to_eval:
            t0 = time.time()
            motor = ComponentConfig(
                'motor', component_counts[0], rep[0], cdf[0])
            elec = ComponentConfig(
                'elec', component_counts[1], rep[1], cdf[1])
            iron = ComponentConfig(
                'iron', component_counts[2], rep[2], cdf[2])
            pvc = ComponentConfig(
                'pvc', component_counts[3], rep[3], cdf[3])

            motor.gf = create_gfs(component_counts[0], depth[0])
            elec.gf = create_gfs(component_counts[1], depth[1])
            iron.gf = create_gfs(component_counts[2], depth[2])
            pvc.gf = create_gfs(component_counts[3], depth[3])

            name = f'{tas_name}_{cdf_name}_{rep_name}_{today}'

            sim = Config(name, tas)

            sim.motor_config = motor
            sim.elec_config = elec
            sim.iron_config = iron
            sim.pvc_config = pvc
            controller = StatisticalController(name,
                                               tas,
                                               years=YEARS,
                                               timestep=TIMESTEP)
            controller.populate(motor, elec, iron, pvc)
            controller.run(directory=base_dir)

            analysis = StatisticalFailureAnalysis(name)
            for component in [motor, elec, iron, pvc]:
                analysis.failure(component.name,
                                 base_dir,
                                 years=YEARS)
            print(time.time() - t0)
