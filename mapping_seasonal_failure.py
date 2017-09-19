import numpy as np
import os
import sqlite3 as sql
import math

# file1 = open(os.path.expanduser('8-08-17/noTime_yesCC_ironPipeFail.txt'), 'r')
# list1 = file1.read().splitlines()
Path = '9-15-17/noTemp0.db'
db = sql.connect(Path)
com = db.cursor()

failure_list = list()
month_bins = []
c = 0
while c < 60:
    month_bins.append(0)
    c += 1

for item in com.execute('SELECT * FROM failureData ORDER BY Bihour_Count ASC'):
    day_count = float(item[0])
    if (math.floor(day_count / 4380) > 22 and math.floor(day_count / 4380) < 26):
        month = math.floor(((day_count / 4380) - 25) * 12)
        month_bins[month] = month_bins[month] + 1
    
for item in month_bins:
    print(item)