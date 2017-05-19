import os
import sqlite3 as sql
from config_c import *
import epanet_c

# TODO Environment variables for server aren't persisting for some reason
os.remove('D:\\Austin_Michne\\tripleSim\\realistic0.db')
os.remove('D:\\Austin_Michne\\tripleSim\\noTemp0.db')
os.remove('D:\\Austin_Michne\\tripleSim\\noTime0.db')
# Creating all three database
databaseObjectReal = sql.connect(('D:\\Austin_Michne\\tripleSim\\realistic{}.db').format(os.environ['SIMCOUNT']))
databaseCursorReal = databaseObjectReal.cursor()
databaseCursorReal.execute('''CREATE TABLE NodeData (Bihour_Count real, NodeID real, Pressure real)''')
databaseCursorReal.execute('''CREATE TABLE linkData (Bihour_Count real, NodeID real, Pressure real)''')

databaseObject_noTemp = sql.connect(('D:\\Austin_Michne\\tripleSim\\noTemp{}.db').format(os.environ['SIMCOUNT']))
databaseCursor_noTemp = databaseObject_noTemp.cursor()
databaseCursor_noTemp.execute('''CREATE TABLE NodeData (Bihour_Count real, NodeID real, Pressure real)''')
databaseCursor_noTemp.execute('''CREATE TABLE linkData (Bihour_Count real, NodeID real, Pressure real)''')


databaseObject_noTime = sql.connect(('D:\\Austin_Michne\\tripleSim\\noTime{}.db').format(os.environ['SIMCOUNT']))
databaseCursor_noTime = databaseObject_noTime.cursor()
databaseCursor_noTime.execute('''CREATE TABLE NodeData (Bihour_Count real, NodeID real, Pressure real)''')
databaseCursor_noTime.execute('''CREATE TABLE linkData (Bihour_Count real, NodeID real, Pressure real)''')

# Opens the toolkit

batch = 0
batch_noTemp = 0
batch_noTime = 0
while batch < 2525:
    epanet_c.epanet(batch, 'real', databaseCursorReal, databaseObjectReal)
    batch += 1
    epanet_c.epanet(batch_noTemp, 'noTemp', databaseCursor_noTemp, databaseObject_noTemp)
    batch_noTemp += 1
    epanet_c.epanet(batch, 'noTime', databaseCursorReal, databaseObjectReal)
    batch_noTime += 1
    print(batch)
epalib.ENcloseH()
epalib.ENclose()
os.environ['SIMCOUNT'] = str(int(os.environ['SIMCOUNT']) + 1)
