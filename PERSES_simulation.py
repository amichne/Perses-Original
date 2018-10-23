import math
import ctypes as ct


class failure_simulation(object):
    def __init__(self, batch, simType, **kwargs):
        self.alive = True
        self.batch = batch
        self.simType = simType
        # for key, value in kwargs.items():
        self.data = kwargs['data']
        self.time = kwargs['time']
        self.tasMaxACTList = kwargs['tasMaxACTList']
        self.nodeCount = kwargs['nodeCount']
        self.nodeID = kwargs['nodeValue']
        self.normal_run_list = kwargs['normal_run_list']
        self.distList = kwargs['distList']
        self.timestep = kwargs['timestep']
        self.nodeValue = kwargs['nodeValue']
        self.biHourToYear = kwargs['biHourToYear']
        self.pump_rep_time = kwargs['pump_rep_time']
        self.pipe_rep_time = kwargs['pipe_rep_time']

    def EPANET_simulation(self):
        self.epaCount = 0
        biHour = (self.batch * 4380)
        simType = str(self.simType)
        self.time.contents = ct.c_long(0)
        self.nodeValue = ct.pointer(ct.c_float(0.0))
        self.nodeID = ct.c_char_p(('Testing purposes').encode('UTF-8'))

        node_data = list()
        node_data_sub_40 = list()
        node_data_sub_20 = list()
        failure_data = list()

        # Currently set to do year long batches
        while self.epaCount < 4380:
            dayCount = math.floor(biHour / 12)
            # Temperature at Surface maximum at current timestep
            tasMaxACT = float(
                self.tasMaxACTList[simType.split("_")[0]][dayCount])
            # Normal run used to track state of EPANET simulation
            normal_run = 1
            # Comp = Component, iterates over all component types in the simulation
            comps = list(filter(lambda x: x != "epanet",
                                self.data[self.simType]))
            for comp in comps:
                # Iterates over all instances of each component type, eg. PVC_1, PVC_2, etc, for all PVC
                for index, item in enumerate(self.data[self.simType][comp]['fS']):
                    # If the pipe is already in the failed state
                    if self.data[self.simType][comp]['fS'][index] != 0:
                        self.data[self.simType][comp]['fS'][index] = int(
                            self.data[self.simType][comp]['fS'][index]) - 1
                        if (int(self.data[self.simType][comp]['fS'][index]) <= 0):
                            # Turning the pipe back on in the simulation
                            self.data[self.simType]['epanet'].ENsetlinkvalue(
                                self.data[self.simType][comp]['index'][index], ct.c_int(11), ct.c_float(1.0))
                            # no-time simulation config stuff
                            if self.simType != "noTime":
                                self.reset_exposure(self.simType, comp, index)
                        else:
                            # Component disable mid run
                            normal_run = 0
                            self.data[self.simType]['epanet'].ENsetlinkvalue(
                                self.data[self.simType][comp]['index'][index], ct.c_int(11), ct.c_float(0.0))
                    # noTime has a special set of configurations, just ignore
                    # Testing if component is not failed, can't fail already failed component
                    if (self.simType == 'noTime' or self.data[self.simType][comp]['fS'][index]) == 0:
                        # Failure determination module, can be modified for individual uses
                        failure_det = self.failure_evaluation(
                            comp, index, tasMaxACT)
                        # If the component should be failed, we turn it off and record the failure in both locations
                        if (failure_det == True):
                            self.data[self.simType]['epanet'].ENsetlinkvalue(
                                self.data[self.simType][comp]['index'][index], ct.c_int(11), ct.c_float(0.0))
                            failure_data.append(tuple([biHour, index, comp]))
                            # It is now an abnormal run, and we set the failure state of the component according to given values
                            normal_run = 0
                            if (comp != 'pump'):
                                self.data[self.simType][comp]['fS'][index] = self.pipe_rep_time
                            else:
                                self.data[self.simType][comp]['fS'][index] = self.pump_rep_time
        # Does the hydraulic solving via EPANET, saves the results in our DB
            if (normal_run == 0):
                self.data[self.simType]['epanet'].ENrunH(self.time)
                intCount = 1
                while (intCount < self.nodeCount.contents.value):
                    self.data[self.simType]['epanet'].ENgetnodevalue(
                        ct.c_int(intCount), ct.c_int(11), self.nodeValue)
                    self.data[self.simType]['epanet'].ENgetnodeid(
                        ct.c_int(intCount), self.nodeID)
                    node_data.append(tuple([biHour, (self.nodeID.value).decode(
                        'utf-8'), self.nodeValue.contents.value]))
                    intCount += 1
            else:
                if (len(self.normal_run_list[int(biHour % 24)]) == 0):
                    self.data[self.simType]['epanet'].ENrunH(self.time)
                    intCount = 1
                    while (intCount < self.nodeCount.contents.value):
                        self.data[self.simType]['epanet'].ENgetnodevalue(
                            ct.c_int(intCount), ct.c_int(11), self.nodeValue)
                        self.data[self.simType]['epanet'].ENgetnodeid(
                            ct.c_int(intCount), self.nodeID)
                        nodeID = self.nodeID.value.decode('utf-8')
                        nodeValue = self.nodeValue.contents.value
                        data_tuple = tuple([biHour,  nodeID, nodeValue])
                        if nodeValue <= 40:
                            if nodeValue <= 20:
                                node_data_sub_20.append(data_tuple)
                            else:
                                node_data_sub_40.append(data_tuple)
                        node_data.append(data_tuple)
                        self.normal_run_list[int(biHour % 24)].append(
                            [nodeID, nodeValue])
                        intCount += 1
                else:
                    for item in self.normal_run_list[int(biHour % 24)]:
                        node_data.append(tuple([biHour, item[0], item[1]]))
            if (self.time.contents.value == 86400):
                self.time.contents = ct.c_int(0)
            self.data[self.simType]['epanet'].ENnextH(self.timestep)
            biHour += 1
            self.epaCount += 1
        return {"failure_data": failure_data, "node_data": node_data,
                "node_data_sub_20": node_data_sub_20, "node_data_sub_40": node_data_sub_40}

    def failure_evaluation(self, comp, index, tasMaxACT):
        # Pumps have multiple failure mechanisms (electrical and motor), so they have special treatment
        # Everything treated as "lists" for code reusability
        if (comp != 'pump'):
            exp_from_dict = [self.data[self.simType][comp]['exp']]
            ltH_from_dict = [self.data[self.simType][comp]['ltH']]
            ctH_from_dict = [self.data[self.simType][comp]['ctH']]
            failure_dist = [comp]
        else:
            exp_from_dict = [self.data[self.simType][comp]
                             ['motor_exp'], self.data[self.simType][comp]['elec_exp']]
            ltH_from_dict = [self.data[self.simType][comp]
                             ['motor_ltH'], self.data[self.simType][comp]['elec_ltH']]
            ctH_from_dict = [self.data[self.simType][comp]
                             ['motor_ctH'], self.data[self.simType][comp]['elec_ctH']]
            failure_dist = ['motor', 'elec']
        # Use failure flag to signal to w/e called this function
        failure_flag = False
        for fail_type, exp_list in enumerate(exp_from_dict):
            # Exposure calculations used for failure determination
            per_failed1 = self.distList[failure_dist[fail_type]][math.floor(
                float(exp_list[index]))]
            per_failed2 = self.distList[failure_dist[fail_type]][math.ceil(
                float(exp_list[index]))]
            per_failed = (float(per_failed2) - float(per_failed1)) * (
                float(exp_list[index]) - math.floor(float(exp_list[index]))) + float(per_failed1)
            # If component failed, again ignore self.simType testing, very specific use-case
            if (per_failed > float(ctH_from_dict[fail_type][index])):
                if self.simType != "noTime":
                    exp_list[index] = 0
                    indexOfctH = (ltH_from_dict[fail_type][index].index(
                        ctH_from_dict[fail_type][index])) + 1
                    ctH_from_dict[fail_type][index] = ltH_from_dict[fail_type][index][indexOfctH]
                failure_flag = True
                return failure_flag
        if self.simType != "noTime":
            exp_list[index] = float(exp_list[index]) + \
                (self.biHourToYear * tasMaxACT)

        return failure_flag

    def reset_exposure(self, simType, comp, index):
        # Used for resetting exposure, again using lists due to pump failure mechanism
        exp_from_dict = list()
        if (comp != 'pump'):
            exp_from_dict = [self.data[self.simType][comp]['exp']]
        else:
            exp_from_dict = [[self.data[self.simType][comp]
                              ['motor_exp'], self.data[self.simType][comp]['elec_exp']]]
        for fail_type, exp_list in enumerate(exp_from_dict):
            exp_list[index] = 0
