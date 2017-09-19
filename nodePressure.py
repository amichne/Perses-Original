import sqlite3 as sql
import math
import os


Path = '9-15-17/noTemp0.db'
print(Path)
db = sql.connect(Path)
com = db.cursor()
ouCount = 0
ou2Count = 0
pipeFile = open(os.path.expanduser('pipes.txt'), 'r')
pipeList = pipeFile.read().splitlines()
pipeFile.close()
demandList = list()
for index, item in enumerate(pipeList):
    curr = float(item.split()[2])
    iD = float(item.split()[0])
    if (curr > 0):
        demandList.append(iD)

dbOUCount = list()
dbOUCount2 = list()
timeStepCountList = list()
count = 0
infiniteCount = 0
while (infiniteCount < 20):
    dbOUCount.append(0)
    dbOUCount2.append(0)
    infiniteCount += 1
print(demandList)
yrList = list()
list1 = com.execute('SELECT * FROM NodeData ORDER BY Bihour_Count ASC')
for row in list1:
    newItem = float(row[1])
    if (newItem in demandList):
        try:
            ouCount = dbOUCount[math.floor((row[0]) / 4380)]
            ou2Count = dbOUCount2[math.floor((row[0]) / 4380)]
        except Exception:
            dbOUCount.append(0)
            dbOUCount2.append(0)
            ouCount = 0
            ou2Count = 0

        if (float(row[2]) <= 40):
            # print(row)
            if (float(row[2]) <= 20):
                ou2Count += 1
            else:
                ouCount += 1
        try:
            # print("Boi")
            dbOUCount[math.floor((row[0]) / 4380)] = ouCount
            dbOUCount2[math.floor((row[0]) / 4380)] = ou2Count

        except Exception:
            print(row, "Broken")

for item in dbOUCount:
    print(item)
print("\n\n\n")
for item in dbOUCount2:
    print(item)