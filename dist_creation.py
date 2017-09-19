import numpy as np


f_list = ['pvc', 'iron', 'pump']
dict_list = {'pump': {'curve': [], 'count': [], '2h': []}, 'iron': {'curve': [], 'count': [], '2h': []}, 'pvc': {'curve': [], 'count': [], '2h': []}}

for f_ in f_list:
    f_o = open(('{}_made_cdf.txt').format(f_), 'r')
    line_list = f_o.read().splitlines()
    f_o.close()
    count = 0
    line2 = ''
    for line in line_list:
        dict_list[f_]['curve'].append(float(line))
        dict_list[f_]['count'].append(count)
        if line2 != '':
            ig = (float(line) - float(line2)) / (365 * 12)
            count2 = 0
            while count2 < (365 * 12):
                dict_list[f_]['2h'].append(float(count2 * ig))
                count2 += 1

        line2 = float(line)
    f_i = open(('{}_long_cdf.txt').format(f_), 'w')
    for val in dict_list[f_]['2h']:
        f_i.write(('{}\n').format(val))
    f_i.close()
    