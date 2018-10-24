import pandas as pd
from pprint import pprint


class ExcelCdfToCsv:
    workbook = dict()
    sheets = list()
    columns = None
    skiprows = None

    def __init__(self, filepath, sheets, columns, rows):
        self.sheets = sheets
        self.columns = columns
        self.skiprows = rows
        self.workbook = pd.read_excel(
            filepath, sheet_name=sheets, usecols=columns, skiprows=rows, header=None)
        # for sheet in list(self.workbook.values()):
        #     sheet.rename(columns=lambda x: int(float(x)*100.0), inplace=True)
        # sheet.columns = [x * 100 for x in sheet.columns]

    def write_files(self, dir_):
        for sheet, values in list(self.workbook.items()):
            print(values.shape[0], values.shape[1])
            bins = [0] * (50 * values.shape[0])

            for j in range(values.shape[0]):
                for i in range(values.shape[1]):
                    try:
                        bins[j * (i+20)] += float(values[i][j] /
                                                  30) - float(values[i][j-1] / 30)
                    except KeyError:
                        bins[j * (i+20)] += float(values[i][j] / 30)

            fp = sheet.lower().replace(' ', '_') + '.txt'
            wrt_bins = [0] * (50 * values.shape[0])
            for i in range(1, len(wrt_bins)):
                wrt_bins[i] = sum(bins[0:i])
            with open(dir_+'/'+fp, 'w+') as handle:
                handle.writelines([str(val)+"\n" for val in wrt_bins])


if __name__ == "__main__":
    types = ['Iron', 'PVC']
    for type_ in types:
        test = ExcelCdfToCsv('./data/cdf/{}_Weibull_CDFs_20180917.xlsx'.format(type_),
                             ['Best Case {}'.format(type_),
                              'Mid Case {}'.format(type_),
                              'Worst Case {}'.format(type_)], 'C:AG', list(range(10)))
        test.write_files('./data/new_cdf')
    types = ['Electronics', 'Motor']
    for type_ in types:
        test = ExcelCdfToCsv('./data/new_cdf/Pump_Weibull_CDFs_20180917.xlsx',
                             ['Best Case {}'.format(type_),
                              'Mid Case {}'.format(type_),
                              'Worst Case {}'.format(type_)], 'C:AG', list(range(10)))
        test.write_files('./data/new_cdf')
