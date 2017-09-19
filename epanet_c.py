import math
import ctypes as ct
from config_c import *



def epanet(batch, simType, dbCursor, dbObject):
    epaCount = 0
    biHour = (batch * 4380)
    
    time.contents = ct.c_long(0)

    while epaCount < 4380:
        # using 1 hour timesteps? Make sure to fucking fix
        dayCount = math.floor(biHour / 12)
        tasMaxACT = float(tasMaxACTList[simType][dayCount])
        normal_run = 1
        ############### PVC PIPE ##### PVC PIPE ##### PVC PIPE ####################
        for index, item in enumerate(data[simType]['pvc']['index']):
            # If the pipe is already in the failed state
            if (int(data[simType]['pvc']['fS'][index]) != 0):
                data[simType]['pvc']['fS'][index] = int(data[simType]['pvc']['fS'][index]) - 1
                if (int(data[simType]['pvc']['fS'][index]) <= 0):
                    # pipe enable
                    epalib.ENsetlinkvalue(data[simType]['pvc']['index'][index], ct.c_int(11), ct.c_float(1.0))
                    # no-time simulation config stuff
                    if ((simType == 'noTemp') or (simType == 'real')):
                        data[simType]['pvc']['exp'][index] = 0
                # Pipe disable mid run
                else:
                    normal_run = 0
                    epalib.ENsetlinkvalue(data[simType]['pvc']['index'][index], ct.c_int(11), ct.c_float(0.0))
                    
            if ((simType == 'noTime') or (int(data[simType]['pvc']['fS'][index]) == 0)):
                
                per_failed1 = distList['pvc'][math.floor(float(data[simType]['pvc']['exp'][index]))]
                per_failed2 = distList['pvc'][math.ceil(float(data[simType]['pvc']['exp'][index]))]
                per_failed = (float(per_failed2) - float(per_failed1)) * (float(data[simType]['pvc']['exp'][index]) - math.floor(float(data[simType]['pvc']['exp'][index]))) + float(per_failed1)
                if (per_failed > float(data[simType]['pvc']['ctH'][index])):
                    if ((simType == 'noTemp') or (simType == 'real')):
                        data[simType]['pvc']['exp'][index] = 0
                        # data[simType]['pvc']['tH'][index] = (np.random.uniform(0, 1, 1)[0])
                        indexOfctH = data[simType]['pvc']['ltH'][index].index(data[simType]['pvc']['ctH'][index]) + 1
                        data[simType]['pvc']['ctH'][index] = data[simType]['pvc']['ltH'][index][indexOfctH]

                    epalib.ENsetlinkvalue(data[simType]['pvc']['index'][index], ct.c_int(11), ct.c_float(0.0))
                    pipeFailureFile = open(('{}_pvcPipeFail.txt').format(simType), 'a')
                    pipeFailureFile.write('%s %s\n' % (index, biHour))
                    pipeFailureFile.close()
                    dbCursor.execute('''INSERT INTO failureData VALUES (?, ?, ?)''', (biHour, index, 'pvc'))
                    data[simType]['pvc']['fS'][index] = 44
                    # This is based off of the 88 hr repair time, can be
                    # changed to w/e
                if ((simType == 'noTemp') or (simType == 'real')):
                    data[simType]['pvc']['exp'][index] = float(data[simType]['pvc']['exp'][index]) + (biHourToYear * tasMaxACT)

                if (data[simType]['pvc']['fS'][index] == 0):
                    epalib.ENsetlinkvalue(data[simType]['pvc']['index'][index], ct.c_int(11), ct.c_float(1.0))


        #################### IRON PIPE ##### IRON PIPE ##### IRON PIPE ####################
        for index, item in enumerate(data[simType]['iron']['index']):
            # Handling failed components
            if (int(data[simType]['iron']['fS'][index]) != 0):
                data[simType]['iron']['fS'][index] = int(data[simType]['iron']['fS'][index]) - 1
                if (int(data[simType]['iron']['fS'][index]) <= 0):
                    epalib.ENsetlinkvalue(data[simType]['iron']['index'][index], ct.c_int(11), ct.c_float(1.0))

                else:
                    normal_run = 0
                    epalib.ENsetlinkvalue(data[simType]['iron']['index'][index], ct.c_int(11), ct.c_float(0.0))

                if (simType == ('noTemp' or 'real')):
                    data[simType]['iron']['exp'][index] = biHourToYear

            # Currently functional and testing for failure
            if (simType == 'noTime') or (int(data[simType]['iron']['fS'][index]) == 0):
                
                per_failed1 = distList['iron'][math.floor(float(data[simType]['iron']['exp'][index]))]
                per_failed2 = distList['iron'][math.ceil(float(data[simType]['iron']['exp'][index]))]
                per_failed = (float(per_failed2) - float(per_failed1)) * (float(data[simType]['iron']['exp'][index]) - math.floor(float(data[simType]['iron']['exp'][index]))) + float(per_failed1)

                if (per_failed > float(data[simType]['iron']['ctH'][index])):
                    normal_run = 0
                    
                    if ((simType == 'noTemp') or (simType == 'real')):
                        data[simType]['iron']['exp'][index] = 0

                        indexOfctH = data[simType]['iron']['ltH'][index].index(data[simType]['iron']['ctH'][index]) + 1
                        data[simType]['iron']['ctH'][index] = data[simType]['iron']['ltH'][index][indexOfctH]

                    epalib.ENsetlinkvalue(data[simType]['iron']['index'][index], ct.c_int(11), ct.c_float(0.0))
                    # Writing to the seperate failure statistics file
                    pipeFailureFile = open(('{}_ironPipeFail.txt').format(simType), 'a')
                    pipeFailureFile.write('%s %s\n' % (index, biHour))
                    pipeFailureFile.close()
                    dbCursor.execute('''INSERT INTO failureData VALUES (?, ?, ?)''', (biHour, index, 'iron'))
                    # This is based off of the 88 hr repair time, can be
                    # changed to w/e
                    data[simType]['iron']['fS'][index] = 44
                if ((simType == 'noTemp') or (simType == 'real')):
                    data[simType]['iron']['exp'][index] = float(data[simType]['iron']['exp'][index]) + (biHourToYear * tasMaxACT)

                if (data[simType]['iron']['fS'][index] == 0):
                    epalib.ENsetlinkvalue(data[simType]['iron']['index'][index], ct.c_int(11), ct.c_float(1.0))

        ######################### PUMPS ##### PUMPS ##### PUMPS #############################################
        for index, item in enumerate(data[simType]['pump']['index']):
            # If component in failed state
            if (data[simType]['pump']['fS'][index] != 0):
                data[simType]['pump']['fS'][index] = int(data[simType]['pump']['fS'][index]) - 1

                if (int(data[simType]['pump']['fS'][index]) <= 0):
                    epalib.ENsetlinkvalue(data[simType]['pump']['index'][index], ct.c_int(11), ct.c_float(1.0))
                    if ((simType == 'noTemp') or (simType == 'real')):
                        data[simType]['pump']['exp'][index] = 0
                else:
                    epalib.ENsetlinkvalue(data[simType]['pump']['index'][index], ct.c_int(11), ct.c_float(0.0))
                    normal_run = 0

            # Not currently failed block
            if ((simType == "noTime") or (data[simType]['pump']['fS'][index] == 0)):

                per_failed1 = distList['pump'][math.floor(float(data[simType]['pump']['exp'][index]))]
                
                per_failed2 = distList['pump'][math.ceil(float(data[simType]['pump']['exp'][index]))]
                
                per_failed = (float(per_failed2) - float(per_failed1)) * (float(data[simType]['pump']['exp'][index]) - math.floor(float(data[simType]['pump']['exp'][index]))) + float(per_failed1)
                
                if (per_failed > float(data[simType]['pump']['ctH'][index])):
                    normal_run = 0
                    if ((simType == 'noTemp') or (simType == 'real')):
                        data[simType]['pump']['exp'][index] = 0
                        indexOfctH = data[simType]['pump']['ltH'][index].index(data[simType]['pump']['ctH'][index]) + 1
                        data[simType]['pump']['ctH'][index] = data[simType]['pump']['ltH'][index][indexOfctH]

                    pumpFailureFile = open(('{}_pumpFail.txt').format(simType), 'a')
                    pumpFailureFile.write('%s %s\n' % (index, biHour))
                    pumpFailureFile.close()
                    dbCursor.execute('''INSERT INTO failureData VALUES (?, ?, ?)''', (biHour, index, 'pump'))
                    
                    epalib.ENsetlinkvalue(data[simType]['pump']['index'][index], ct.c_int(11), ct.c_float(0.0))
                    
                    data[simType]['pump']['fS'][index] = 8
                if ((simType == 'noTemp') or (simType == 'real')):
                    data[simType]['pump']['exp'][index] = float(data[simType]['pump']['exp'][index]) + float(biHourToYear * tasMaxACT)
                        
                if (data[simType]['pump']['fS'][index] == 0):
                    epalib.ENsetlinkvalue(data[simType]['pump']['index'][index], ct.c_int(11), ct.c_float(1.0))

        # Does the hydraulic solving
        
        if (normal_run == 0):
            epalib.ENrunH(time)
            intCount = 1
            while (intCount < nodeCount.contents.value):
                epalib.ENgetnodevalue(ct.c_int(intCount), ct.c_int(11), nodeValue)
                epalib.ENgetnodeid(ct.c_int(intCount), nodeID)
                dbCursor.execute('''INSERT INTO NodeData VALUES (?, ?, ?)''', (biHour, (nodeID.value).decode('utf-8'), nodeValue.contents.value))
                
                intCount += 1
        else:
            if (len(normal_run_list[int(biHour % 24)]) == 0):
                epalib.ENrunH(time)
                intCount = 1
                while (intCount < nodeCount.contents.value):
                    epalib.ENgetnodevalue(ct.c_int(intCount), ct.c_int(11), nodeValue)
                    epalib.ENgetnodeid(ct.c_int(intCount), nodeID)
                    dbCursor.execute('''INSERT INTO NodeData VALUES (?, ?, ?)''', (biHour, (nodeID.value).decode('utf-8'), nodeValue.contents.value))
                    normal_run_list[int(biHour % 24)].append([(nodeID.value).decode('utf-8'), nodeValue.contents.value])
                    intCount += 1
            else:
                for item in normal_run_list[int(biHour % 24)]:
                    dbCursor.execute('''INSERT INTO NodeData VALUES (?, ?, ?)''', (biHour, item[0], item[1]))
        if (time.contents.value == 86400):
            time.contents = ct.c_int(0)
        epalib.ENnextH(timestep)

        # Saves the hydraulic results file
        # epalib.ENsaveH()
        # Reports the data from the previous run
        # epalib.ENreport()
        # epalib.ENclose()

        # Closes all of the files open during the simulation
        biHour += 1
        epaCount += 1
    dbObject.commit()