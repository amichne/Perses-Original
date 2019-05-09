from os import makedirs
from shutil import rmtree
from getpass import getpass
from datetime import date

from data_analysis.failure_analysis import Components, ComponentFailureAnalysis, FailureAnalysisMemory
from data_analysis.pressure_analysis import NodalPressureAnalysis
from data_analysis.db_util import DatabaseHandle, database_loader


class Analytics:
    db_param = {'user': 'root', 'password': None,
                'db': None, 'host': 'localhost'}
    sim_name = None
    sim_params = {'temp': None, 'rep': None, 'cdf': None}
    base_dir = None
    db = None

    def __init__(self, sim_name, pass_, sim_params=None, base_dir='output', date_tag=True):
        self.sim_name = sim_name
        self.db_param['password'] = pass_
        self.db_param['db'] = self.sim_name
        self.db = database_loader(self.db_param)
        if date_tag:
            base_dir += date.today().strftime('%Y%m%d')
        self.base_dir = base_dir
        self.dir_gen()

    def dir_gen(self):
        dir_ = '{}/{}/pressure'.format(self.base_dir, self.sim_name)
        makedirs(dir_, exist_ok=True)
        dir_ = '{}/{}/failure'.format(self.base_dir, self.sim_name)
        makedirs(dir_, exist_ok=True)

    def run(self, thresholds={'fail': 20, 'disfunc': 40},
               offsets={'fail': 43800, 'disfunc': 45260},
            identified=True, deidentified=True):
        fail = ComponentFailureAnalysis(self.db, self.sim_name)
        for comp in ['pvc', 'iron', 'pump']:
            fail.write_failure(comp, self.base_dir, identified, deidentified)
        pressure = NodalPressureAnalysis(self.db, self.sim_name)
        for tag, thresh in list(thresholds.items()):
            data = pressure.outages(thresh, offsets[tag])
            pressure.write_ann(data, thresh, base_dir=self.base_dir)
            pressure.write_cum_ann(data, thresh, base_dir=self.base_dir)

    def failure(self, identified=True, deidentified=True):
        fail = ComponentFailureAnalysis(self.db, self.sim_name)
        for comp in ['pvc', 'iron', 'pump']:
            fail.write_failure(comp, self.base_dir, identified, deidentified)

    def clean(self, drop_database=True, exclude_tables=[]):
        if drop_database:
            self.db.drop_self()
        else:
            self.db.drop_tables(exclude=exclude_tables)
