import numpy as np
import os
import sqlite3 as sql

# file1 = open(os.path.expanduser('8-08-17/noTime_yesCC_ironPipeFail.txt'), 'r')
# list1 = file1.read().splitlines()
Path = '9-15-17/realistic0.db'
db = sql.connect(Path)
com = db.cursor()



yearList = list()
breakCountpvc = list()
breakCountiron = list()
breakCountpump = list()
count = 0
while count < 83:
    yearList.append(count)
    breakCountpvc.append(0)
    breakCountiron.append(0)
    breakCountpump.append(0)
    count += 1

for item in com.execute('SELECT * FROM failureData ORDER BY Bihour_Count ASC'):
    thisIndex = int(np.floor((int(item[0]) / 4380)))
    if item[2] == "pvc":
        breakCountpvc[thisIndex] = breakCountpvc[thisIndex] + 1
    if item[2] == "iron":
        breakCountiron[thisIndex] = breakCountiron[thisIndex] + 1
    if item[2] == "pump":
        breakCountpump[thisIndex] = breakCountpump[thisIndex] + 1

for index, iteam in enumerate(breakCountpvc):
    print(('{}').format(breakCountpvc[index]))

print('\n\n\n')
for index, iteam in enumerate(breakCountpump):
    print(('{}').format(breakCountpump[index]))
print('\n\n\n')
for index, iteam in enumerate(breakCountiron):
    print(('{}').format(breakCountiron[index]))
