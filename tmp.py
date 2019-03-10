files = ['data/temperature/2017_2099_rcp_4.5_min.csv',
         'data/temperature/2017_2099_rcp_8.5_min.csv',
         'data/temperature/2017_2099_rcp_4.5_avg.csv',
         'data/temperature/2017_2099_rcp_8.5_avg.csv',
         'data/temperature/2017_2099_rcp_4.5_max.csv',
         'data/temperature/2017_2099_rcp_8.5_max.csv']

for file in files:
    with open(file, 'r') as handle:
        lines = handle.read().splitlines()
    lines = [line.split(',') for line in lines]
    for line_num in range(len(lines)):
        if len(lines[line_num]) == 2:
            lines[line_num] = lines[line_num][1]
        else:
            lines[line_num] = lines[line_num][0]

    with open(file, 'w') as handle:
        for line in lines:
            handle.write(line + '\n')
