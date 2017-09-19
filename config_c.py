import numpy as np
import ctypes as ct
import math

epalib = ct.cdll.LoadLibrary('epanet2mingw64.dll')
biHourToYear = float(.0002283105022831050228310502283105)
biHour = 0

data = {'real':{'iron':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pvc':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pump':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}}, 'noTemp': {'iron':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pvc':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pump':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}}, 'noTime_yesCC': {'iron':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pvc':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pump':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}}, 'noTime_noCC': {'iron':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pvc':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}, 'pump':{'ctH':list(), 'ltH': list(), 'exp':list(), 'fS':list(), 'index':list(), 'prob': list()}}}

normal_run_list = [list()]*24

tasFile = open('tasMaxBD85.txt', 'r')
tasList = tasFile.read().expandtabs().splitlines()
tasFile.close()

histTasFile = open('histTasMaxBD.txt', 'r')
histTasList = histTasFile.read().expandtabs().splitlines()
histTasFile.close()
tasMaxACTList = {'real': list(tasList), 'noTime_yesCC': list(tasList), 'noTime_noCC': list(histTasList), 'noTemp': list(histTasList)}

f = open('north_marin_c.inp', 'r')
fi = open('placeholder.rpt', 'w')

# Initializes the files for encoding
a = 'north_marin_c.inp'
b = 'placeholder.rpt'

# Byte objects
b_a = a.encode('UTF-8')
b_b = b.encode('UTF-8')

epalib.ENopen(b_a, b_b, "")
epalib.ENopenH()
timestep = ct.pointer(ct.c_long(7200))
time = ct.pointer(ct.c_long(0))
init_flag = ct.c_int(1)
epalib.ENinitH(init_flag)

nodeCount = ct.pointer(ct.c_int(0))
epalib.ENgetcount(ct.c_int(0), nodeCount)
nodeValue = ct.pointer(ct.c_float(0.0))
nodeID = ct.c_char_p(('Testing purposes').encode('UTF-8'))

linkList = ct.pointer(ct.c_int(0))
epalib.ENgetcount(ct.c_int(2), linkList)
linkCounter = 1
currentRough = ct.pointer(ct.c_float(0.0))


# TODO Right now the config for failure is to fail between pump && node, not reservoir && pump
# int appended to list from int pointer return of 'ENgetlinkindex'
indexReturn1 = ct.pointer(ct.c_int(0))
# For the first pipe out of pump 10
linkID = ct.c_char_p(str(10).encode('utf-8'))
epalib.ENgetlinkindex(linkID, indexReturn1)
data['real']['pump']['index'].append(indexReturn1.contents)
data['noTemp']['pump']['index'].append(indexReturn1.contents)
data['noTime_yesCC']['pump']['index'].append(indexReturn1.contents)
data['noTime_noCC']['pump']['index'].append(indexReturn1.contents)
# For the first pipe out of pump 335
linkID = ct.c_char_p(str(335).encode('utf-8'))
indexReturn2 = ct.pointer(ct.c_int(0))
epalib.ENgetlinkindex(linkID, indexReturn2)
data['real']['pump']['index'].append(indexReturn2.contents)
data['noTemp']['pump']['index'].append(indexReturn2.contents)
data['noTime_yesCC']['pump']['index'].append(indexReturn2.contents)
data['noTime_noCC']['pump']['index'].append(indexReturn2.contents)

# Roughness look to determine pipe type
# Using pure c integers in the lists
while (linkCounter < linkList.contents.value):
    indexVal = ct.c_int(linkCounter)
    epalib.ENgetlinkvalue(indexVal, ct.c_int(2), currentRough)
    # Filtering the pumps
    if linkCounter != (indexReturn1.contents.value or indexReturn2.contents.value):
        if (int(currentRough.contents.value) > 140):
            # randironAge = float(np.random.uniform(0, 72, 1)[0])
            # randironAge2 = float(90)
            data['real']['iron']['exp'].append(0)
            data['noTemp']['iron']['exp'].append(0)
            data['noTime_yesCC']['iron']['exp'].append(0)
            data['noTime_noCC']['iron']['exp'].append(0)

            data['real']['iron']['fS'].append(0)
            data['noTemp']['iron']['fS'].append(0)
            data['noTime_yesCC']['iron']['fS'].append(0)
            data['noTime_noCC']['iron']['fS'].append(0)

            ltH = list(np.random.uniform(0, 1, 50000))
            ctH = float(ltH[0])
            data['real']['iron']['ltH'].append(ltH)
            data['real']['iron']['ctH'].append(ctH)
            data['noTemp']['iron']['ltH'].append(ltH)
            data['noTemp']['iron']['ctH'].append(ctH)
            data['noTime_yesCC']['iron']['ltH'].append(ltH)
            data['noTime_yesCC']['iron']['ctH'].append(ctH)
            data['noTime_noCC']['iron']['ltH'].append(ltH)
            data['noTime_noCC']['iron']['ctH'].append(ctH)

            data['real']['iron']['index'].append(indexVal)
            data['noTemp']['iron']['index'].append(indexVal)
            data['noTime_yesCC']['iron']['index'].append(indexVal)
            data['noTime_noCC']['iron']['index'].append(indexVal)

        elif (int(currentRough.contents.value) < 140):
            

            randNonAgingPVC = float(36)
            data['real']['pvc']['exp'].append(0)
            data['noTemp']['pvc']['exp'].append(0)
            data['noTime_yesCC']['pvc']['exp'].append(0)
            data['noTime_noCC']['pvc']['exp'].append(0)

            data['real']['pvc']['fS'].append(0)
            data['noTemp']['pvc']['fS'].append(0)
            data['noTime_yesCC']['pvc']['fS'].append(0)
            data['noTime_noCC']['pvc']['fS'].append(0)

            ltH = list(np.random.uniform(0, 1, 50000))
            ctH = float(ltH[0])
            data['real']['pvc']['ltH'].append(ltH)
            data['real']['pvc']['ctH'].append(ctH)
            data['noTemp']['pvc']['ltH'].append(ltH)
            data['noTemp']['pvc']['ctH'].append(ctH)
            data['noTime_yesCC']['pvc']['ltH'].append(ltH)
            data['noTime_yesCC']['pvc']['ctH'].append(ctH)
            data['noTime_noCC']['pvc']['ltH'].append(ltH)
            data['noTime_noCC']['pvc']['ctH'].append(ctH)

            data['real']['pvc']['index'].append(indexVal)
            data['noTemp']['pvc']['index'].append(indexVal)
            data['noTime_yesCC']['pvc']['index'].append(indexVal)
            data['noTime_noCC']['pvc']['index'].append(indexVal)

    linkCounter += 1

data['real']['pump']['exp'] = list([0, 0])
data['noTemp']['pump']['exp'] = list([0, 0])
# data['noTime_yesCC']['pump']['exp'] = list([5.5, 5.25])
# data['noTime_noCC']['pump']['exp'] = list([5.5, 5.25])

ltH1 = list(np.random.uniform(0, 1, 50000))
ctH1 = float(ltH1[0])
ltH2 = list(np.random.uniform(0, 1, 50000))
ctH2 = float(ltH2[0])
data['real']['pump']['ltH'] = [ltH1, ltH2]
data['real']['pump']['ctH'] = [ctH1, ctH2]
data['noTemp']['pump']['ltH'] = [ltH1, ltH2]
data['noTemp']['pump']['ctH'] = [ctH1, ctH2]
data['noTime_yesCC']['pump']['ltH'] = [ltH1, ltH2]
data['noTime_yesCC']['pump']['ctH'] = [ctH1, ctH2]
data['noTime_noCC']['pump']['ltH'] = [ltH1, ltH2]
data['noTime_noCC']['pump']['ctH'] = [ctH1, ctH2]

data['real']['pump']['fS'] = list([0, 0])
data['noTemp']['pump']['fS'] = list([0, 0])
data['noTime_yesCC']['pump']['fS'] = list([0, 0])
data['noTime_noCC']['pump']['fS'] = list([0, 0])

pvcWeibullFile = open('pvc_made_cdf.txt', 'r')
pvcWeibullList = pvcWeibullFile.read().splitlines()
pvcWeibullFile.close()

ironWeibullFile = open('iron_made_cdf.txt', 'r')
ironWeibullList = ironWeibullFile.read().splitlines()
ironWeibullFile.close()

pumpWeibullFile = open('pump_made_cdf.txt', 'r')
pumpWeibullList = pumpWeibullFile.read().splitlines()
pumpWeibullFile.close()

simList = ['real', 'noTemp', 'noTime_yesCC', 'noTime_noCC']
compList = ['pump', 'pvc', 'iron']
distList = {'pump': pumpWeibullList, 'pvc': pvcWeibullList, 'iron': ironWeibullList}

# for simI in simList:
#     for compType in compList:
#         for index, item in enumerate(data[simI][compType]['exp']):
#             data[simI][compType]['prob'].append({'averageTemp': 29.86, 'count': 1})
#             ageLeft = data[simI][compType]['exp'][index]
#             while (ageLeft > 0):
#                 ageToUse = int(math.floor(ageLeft * 365 * 12))
#                 tasMaxACT = float(histTasList[len(histTasList) - ageToUse - 1])
#                 # indexSelect = (math.trunc(tasMaxACT) - 20)
#                 # if indexSelect < 0:
#                 #     indexSelect = 0
#                 # indexSelect = indexSelect + (30 * int(math.trunc(float(ageLeft))))
#                 # tempDecimal = (((tasMaxACT - math.trunc(tasMaxACT)) / tasMaxACT) * float(weibList[compType][indexSelect]))
#                 # ageDecimal = (((data[simI][compType]['exp'][index] - math.trunc(data[simI][compType]['exp'][index])) / data[simI][compType]['exp'][index]) * float(weibList[compType][indexSelect]))

#                 # weibullApprox = float(weibList[compType][indexSelect]) + tempDecimal + ageDecimal
#                 if isinstance((ageLeft * 365), int):
#                     data[simI][compType]['prob'][index]['averageTemp'] = (data[simI][compType]['prob'][index]['averageTemp'] * data[simI][compType]['prob'][index]['count'] + tasMaxACT) / (data[simI][compType]['prob'][index]['count'] + 1)

#                     data[simI][compType]['prob'][index]['count'] += 1
#                 ageLeft = ageLeft - biHourToYear
#             # if (data[simI][compType]['prob'][index] > data[simI][compType]['ctH'][index]):
#             #     data[simI][compType]['prob'][index] = 0
#             #     newctHindex = data[simI][compType]['ltH'][index].index(data[simI][compType]['ctH'][index]) + 1
#             #     data[simI][compType]['ctH'][index] = data[simI][compType]['ltH'][index][newctHindex]