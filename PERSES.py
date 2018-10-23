import dill
import os
import sqlite3 as sql
import atexit
# All code in PERSES_configuration must be ran before PERSES can funtion, DO NOT alter this line
from PERSES_configuration import *
from PERSES_simulation import failure_simulation


if __name__ == "__main__":
    conn_dict = dict()
    cursor_dict = dict()
    for sim_with_rep in sim_list_strings:
        for comp_type in comps:
            f_ = open(('{}_{}_fail.txt').format(sim_with_rep, comp_type), 'w')
            f_.close()
        try:
            os.remove(('{}.db').format(sim_with_rep))
        except Exception as exp:
            print('No database here')
        conn_dict[sim_with_rep] = sql.connect(('{}.db').format(sim_with_rep))
        cursor_dict[sim_with_rep] = conn_dict[sim_with_rep].cursor()
        cursor_dict[sim_with_rep].execute(
            '''CREATE TABLE NodeData (Bihour_Count real, NodeID real, Pressure real)''')
        cursor_dict[sim_with_rep].execute(
            '''CREATE TABLE NodeDataVLow (Bihour_Count real, NodeID real, Pressure real)''')
        cursor_dict[sim_with_rep].execute(
            '''CREATE TABLE NodeDataMLow (Bihour_Count real, NodeID real, Pressure real)''')
        cursor_dict[sim_with_rep].execute(
            '''CREATE TABLE failureData (Bihour_Count real, NodeID real, componentType real)''')
    batch = 0

    # Doing batched simulations
    # TODO: Parallelize this code
    cursors = list(cursor_dict.values())
    conns = list(conn_dict.values())
    while batch < 150:
        res = []
        simulation_list = []
        for sim_with_rep in sim_list_strings:
            sim_item = failure_simulation(batch, sim_with_rep,
                                          data=data,
                                          time=time,
                                          tasMaxACTList=tasMaxACTList,
                                          nodeCount=nodeCount,
                                          nodeValue=nodeValue,
                                          nodeID=nodeID,
                                          normal_run_list=normal_run_list,
                                          distList=distList[sim_with_rep.split('_')[
                                              1]],
                                          timestep=timestep,
                                          biHourToYear=biHourToYear,
                                          pipe_rep_time=44,
                                          pump_rep_time=8)
            simulation_list.append(sim_item)
        for sim in simulation_list:
            res.append(sim.EPANET_simulation())
        for index in range(0, len(res)):
            cursors[index].executemany(
                '''INSERT INTO failureData VALUES (?, ?, ?)''', res[index]['failure_data'])
            conns[index].commit()
            cursors[index].executemany(
                '''INSERT INTO NodeData VALUES (?, ?, ?)''', res[index]['node_data'])
            conns[index].commit()
            cursors[index].executemany(
                '''INSERT INTO NodeDataVLow VALUES (?, ?, ?)''', res[index]['node_data_sub_20'])
            conns[index].commit()
            cursors[index].executemany(
                '''INSERT INTO NodeDataMLow VALUES (?, ?, ?)''', res[index]['node_data_sub_40'])
            conns[index].commit()
            for comp in comps:
                write_list = filter(
                    lambda x: x[2] == comp, res[index]['failure_data'])
                with open(("{}_{}_fail.txt").format(sim_list_strings[index], comp), 'a') as handle:
                    for value in write_list:
                        handle.write(("{} {}\n").format(value[1], value[0]))
        # for sim in data:
            # data[sim]["epanet"].ENcloseH()
            # data[sim]["epanet"].ENclose()
        print(batch)
        batch += 1
