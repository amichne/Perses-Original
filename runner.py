from hydraulic_simulation.controller import Controller
from hydraulic_simulation.data_util import ComponentConfig, TasMaxProfile

net_file = "north_marin_c.inp"
output_file = "output/output_nmc.rpt"

comps = ComponentConfig("data/cdf/elec_best_cdf.txt", "data/cdf/motor_best_cdf.txt",
                        "data/cdf/iron_best_cdf.txt", "data/cdf/pvc_best_cdf.txt")
tasmax = TasMaxProfile('data/temperature/2017_2099_rcp_4.5_avg.csv')

example = Controller(net_file, output_file, tasmax)

example.populate_epa(comps)

print("Pipe Count: ", len(example.pipes), "\tPump Count: ", len(example.pumps))
