import sqlite3 as sql
import math
import numpy as np
import os


class component_populations:
    exposure_array = list()
    temp_curve = list()
    distribution_list = list()
    god_factor_list = list()
    component_type = None
    biHourToYear = float(.0002283105022831050228310502283105)
    db_cur = None


    def __init__(self, temp_curve_file, failure_dist_file, component_type, amount, db_cur):
        self.component_type = component_type
        self.db_cur = db_cur
        f_ = open(temp_curve_file, 'r')
        f_list = f_.read().splitlines()
        f_.close()
        self.temp_curve = f_list

        f_ = open(failure_dist_file, 'r')
        f_list = f_.read().splitlines()
        f_.close()
        self.distribution_list = f_list

        count = 0
        while (count < amount):
            self.god_factor_list.append(float(np.random.uniform(0, 1)))
            self.exposure_array.append(0)
            count += 1
    

    def failure_evaluation(self, index, time, time2):
        per_failed1 = self.distribution_list[math.floor(float(self.exposure_array[index]))]
        per_failed2 = self.distribution_list[math.ceil(float(self.exposure_array[index]))]
        per_failed = (float(per_failed2) - float(per_failed1)) * (float(self.exposure_array[index]) - math.floor(float(self.exposure_array[index]))) + float(per_failed1)

        if (per_failed > self.god_factor_list[index]):
            self.db_cur.execute('''INSERT INTO failureData VALUES (?, ?, ?)''', (time2, index, self.component_type))
            self.exposure_array[index] = 0
        else:
            self.exposure_array[index] = self.exposure_array[index] + (self.biHourToYear * float(self.temp_curve[time]))

if __name__ == "__main__":
    db_cur_list_labels = ["histTasMaxBD", "tasMaxBD", "tasMaxBD85"]
    db_cur_list = list()
    db_obj_list = list()
    for item in db_cur_list_labels:
        try:
            os.remove(("{}.db").format(item))
        except Exception as exp:
            print('No database here')
        db_obj = sql.connect(("{}.db").format(item))
        db_cur = db_obj.cursor()
        db_cur.execute('''CREATE TABLE failureData (Bihour_Count real, NodeID real, componentType real)''')
        db_cur_list.append(db_cur)
        db_obj_list.append(db_obj)

    statistics_list = list()
    pop_list = ["pump", "pvc", "iron"]
    for simulation_index, simulation in enumerate(db_cur_list):
        for index, item in enumerate(pop_list):
            statistics_list.append(component_populations(("{}.txt").format(db_cur_list_labels[index]), \
                ("{}_made_cdf.txt").format(item), item, 100, simulation))
        time = 0
        goal_time = 350000
        while time < goal_time:
            for population in statistics_list:
                for index, value in enumerate(population.god_factor_list):
                    population.failure_evaluation(index, math.floor(time / 12), time)
            time += 1
        db_obj_list[simulation_index].commit()
        db_obj_list[simulation_index].close()
