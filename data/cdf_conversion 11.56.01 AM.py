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

    def write_files(self, dir_, lowest_temp=20, cdf_count=30):
        for sheet, values in list(self.workbook.items()):
            print(values.shape[0], values.shape[1])
            bins = [0] * (50 * values.shape[0])

            for j in range(1, values.shape[0]):
                for i in range(values.shape[1]):
                    try:
                        bins[j * (i+lowest_temp)] += float(values[i][j] /
                                                           cdf_count) - float(values[i][j-1] / cdf_count)
                    except KeyError:
                        bins[j * (i+lowest_temp)] += float(values[i]
                                                           [j] / cdf_count)

            fp = sheet.lower().replace(' ', '_') + '.txt'
            wrt_bins = [0] * (50 * values.shape[0])
            for i in range(1, len(wrt_bins)):
                wrt_bins[i] = sum(bins[0:i])
            with open(dir_+'/'+fp, 'w+') as handle:
                handle.writelines([str(val)+"\n" for val in wrt_bins])


if __name__ == "__main__":
    types = ['Iron', 'PVC']
    for type_ in types:
        test = ExcelCdfToCsv('./data/current_cdf/{}_Weibull_CDFs_20181217.xlsx'.format(type_),
                             ['Best Case {}'.format(type_),
                              'Mid Case {}'.format(type_),
                              'Worst Case {}'.format(type_)], 'C:AG', list(range(9)))
        test.write_files('./data/current_cdf')
    types = ['Electronics', 'Motor']
    for type_ in types:
        test = ExcelCdfToCsv('./data/current_cdf/Pump_Weibull_CDFs_20181217.xlsx',
                             ['Best Case {}'.format(type_),
                              'Mid Case {}'.format(type_),
                              'Worst Case {}'.format(type_)], 'C:AG', list(range(9)))
        test.write_files('./data/current_cdf')
