from typing import List

from epanettools import epanet2 as et
# from hydraulic_simulation.epanet import et
from components import Pump, Pipe, Node
from component_props import Exposure, Status
from data_util import CumulativeDistFailure, TasMaxProfile, ComponentConfig
from db_util import DatabaseHandle


class Controller:
    # cdf_list: List[CumulativeDistFailure] = list()
    tasmax = None
    pumps = list()
    pipes = list()
    nodes = list()
    current_time = 0
    current_temp = 0.0
    timestep = 7200

    def __init__(self, network, output, tasmax):
        et.ENopen(network, output, '')
        self.tasmax = tasmax

    def populate(self, conf: ComponentConfig):
        for i in range(1, et.ENgetcount(et.EN_LINKCOUNT)[1]+1):
            link_type = et.ENgetlinktype(i)[1]
            if link_type in [0, 1]:
                self.pipes.append(Pipe(i, self.timestep))
                # TODO: Include roughness test for PVC vs IRON
                self.pipes[-1].exp = Exposure(*conf.exp_vals("pvc"))
                self.pipes[-1].status = Status(conf.repair_vals("pipe"))
                self.pipes[-1].timestep = self.timestep
                self.pipes[-1].get_endpoints()
            elif link_type == 2:
                self.pumps.append(Pump(i, self.timestep))
                self.pumps[-1].exp_elec = Exposure(*conf.exp_vals("elec"))
                self.pumps[-1].exp_motor = Exposure(*conf.exp_vals("motor"))
                self.pumps[-1].status_elec = Status(conf.repair_vals("elec"))
                self.pumps[-1].status_motor = Status(conf.repair_vals("motor"))
                self.pumps[-1].timestep = self.timestep
        for i in range(1, et.ENgetcount(et.EN_NODECOUNT)[1]+1):
            self.nodes.append(Node(i))

    def run(self):
        et.ENopenH()
        et.ENinitH(0)
        while True:
            if not self.iterate():
                return

    def iterate(self):
        time = et.ENrunH()[1]
        if (time % self.timestep == 0):
            self.current_time = time
            if (self.current_time % 86400 == 0):
                self.current_temp = self.tasmax.temp(self.current_time)
            for node_ in self.nodes:
                node_.save_pressure(self.current_time)
            self.increment_population()

        if et.ENnextH()[1] <= 0:
            return False
        return True

    def increment_population(self):
        for pump_ in self.pumps:
            pump_.bimodal_eval(self.current_temp, self.current_time)
        for pipe_ in self.pipes:
            pipe_.eval(self.current_temp, self.current_time)

    def write_sql(self, db_param):
        db = DatabaseHandle(**db_param)
        name = db_param['db']
        exec_str = '''
                    DROP DATABASE
                    IF EXISTS {}
                    '''.format(name)
        db.cursor.execute(exec_str)
        db.connection.commit()
        exec_str = '''CREATE DATABASE {}'''.format(name)
        db.cursor.execute(exec_str)
        db.connection.commit()
        print("Dropped and Created Database {}".format(name))
        exec_str = '''
                    CREATE TABLE {}.pressure
                    (node_id CHAR(5), pressure DOUBLE, time INT)
                   '''.format(name)
        db.cursor.execute(exec_str)
        db.connection.commit()
        exec_str = '''
                    CREATE TABLE {}.failure
                    (link_id CHAR(5), time INT, type TINYINT)
                   '''.format(name)
        db.cursor.execute(exec_str)
        db.connection.commit()
        exec_str = '''
                    CREATE TABLE {}.outage
                    (link_id CHAR(5), time INT, type TINYINT)
                   '''.format(name)
        db.cursor.execute(exec_str)
        db.connection.commit()
        # ####################
        exec_str = '''
                    INSERT INTO {}.pressure
                    (node_id, pressure, time)
                    values (%s, %s, %s)
                   '''.format(name)
        tmp_pres = list()
        for node_ in self.nodes:
            tmp_pres.extend(node_.pressure)
        db.cursor.executemany(exec_str, tmp_pres)
        # db.connection.commit()
        print(len(tmp_pres))
        tmp_pres[:] = []
        # ####################
        tmp_lnk = list()
        for link_ in (self.pipes+self.pumps):
            tmp_lnk.extend(link_.failure)
        exec_str = '''
                    INSERT INTO {}.failure
                    (link_id, time, type)
                    values (%s, %s, %s)
                   '''.format(name)
        db.cursor.executemany(exec_str, tmp_lnk)
        db.connection.commit()
        print(len(tmp_lnk))
        tmp_lnk[:] = []
