from getpass import getpass
from epanettools import epanet2 as et

from controller import Controller
from data_util import ComponentConfig, TasMaxProfile

net_file = "../data/north_marin_c.inp"
# net_file = "../data/short_nm.inp"
output_file = "../output/output_nmc.rpt"

comps = ComponentConfig("../data/cdf/elec_best_cdf.txt", "../data/cdf/motor_best_cdf.txt",
                        "../data/cdf/iron_best_cdf.txt", "../data/cdf/pvc_best_cdf.txt")
tasmax = TasMaxProfile('../data/temperature/2017_2099_rcp_4.5_avg.csv')

with Controller(net_file, output_file, tasmax) as example:
    example.populate(comps)
    print("Pipe Count: ", len(example.pipes),
          "\tPump Count: ", len(example.pumps))

    example.run(sql_yr_w=5)

pass__ = getpass()
params = {'user': 'root', 'db': 'example',
          'host': 'localhost', 'password': pass__}
# example.write_sql(params)

# pres_by_node = dict({(node_.id_, tuple(node_.pressure))
#  for node_ in example.nodes})
# json.dump(pres_by_node, open('../output/pressure_by_node.json', 'w+'))