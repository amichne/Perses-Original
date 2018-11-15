from epanettools import epanet2 as et

# x = et.ENopen('./data/north_marin_c.inp', 'net3.rpt', '')
inp = './data/short_nm.inp'
rpt, bn = './data/report/short_nm.rpt', ''
et.ENopen(inp, rpt, bn)
nodes = list()
time = list()

for i in range(et.ENgetcount(et.EN_NODECOUNT)[1]):
    nodes.append(et.ENgetnodeid(i+1)[1])
    print(et.ENgetnodetype(i+1)[1])
pres = [[]]*len(nodes)


# et.ENsettimeparam(0, 32396400)
# et.ENsaveinpfile(inp)
# et.ENclose()
# et.ENopen(inp, rpt, bn)

et.ENopenH()
et.ENinitH(0)

# et.ENsetlinkvalue(5, et.EN_STATUS, 0)
print("Link nodes", et.ENgetlinknodes(5)[1::])
print("Link type", et.ENgetlinktype(5)[1])
print("Link ID", et.ENgetlinkid(5))

count = 0
while True:
    t = et.ENrunH()[1]
    if (t % 3600) == 0:
        time.append(t)
        count += 1
    # Retrieve hydraulic results for time t
    # for i in range(len(nodes)):
    # pres[1].append(et.ENgetnodevalue(1, et.EN_PRESSURE))
    et.ENreport()
    if (et.ENnextH()[1] <= 0):
        break

et.ENcloseH()
# print(["{}\n".format(x) for x in pres], file=open('tmp.pres', 'w+'))

print(count)
print(len(time), time)
print(len(list(set(time))))
