from hydraulic_simulation.db_util import DatabaseHandle


class Controller:
    tmp_dir = None
    tasmax = None
    pumps = None
    pipes = None
    nodes = None
    current_time = None
    current_temp = None
    timestep = None
    time = 0
    year = 60 * 60 * 24 * 365
    db_handle = None

    def __init__(self, output, tasmax, years=82, timestep=60*60, tmp_dir='data/tmp/'):
        ''' Initializes the EPANET simulation, as well adding a two day
            buffer to the network file, and saving in a temp location.
            This temp network with the buffer will be deleted upon class
            destruction.
        '''
        self.timestep = timestep
        self.time = ((48 * 60 * 60) + (years * self.year))

        self.tasmax = tasmax
        self.pumps = list()
        self.pipes = list()
        self.nodes = list()
        self.current_time = 0
        self.current_temp = 0.0
        self.tmp_dir = tmp_dir

    def create_db(self, db_handle, pressure=True, failure=True, outages=True):
        self.db_handle = db_handle
        self.db_handle.reset_db()

        if pressure:
            pressure_schema = '(node_id CHAR(5), pressure DOUBLE, time INT UNSIGNED)'
            self.db_handle.create_table('pressure', pressure_schema)

        if failure:
            failure_schema = '(link_id CHAR(5), time INT UNSIGNED, type char(5))'
            self.db_handle.create_table('failure', failure_schema)

        if outages:
            outage_schema = '(link_id CHAR(5), time INT UNSIGNED, type char(5))'
            self.db_handle.create_table('outage', outage_schema)

        print("Table created for run: " + self.db_handle.db)

    def pressure_to_sql(self):
        tmp_pres = list()
        for node_ in self.nodes:
            tmp_pres.extend(node_.pressure)
            node_.pressure.clear()
        for index in range(len(tmp_pres)):
            tmp_pres[index][2] = tmp_pres[index][2] / self.timestep
        self.db_handle.insert(tmp_pres, 'pressure',
                              '(node_id, pressure, time)')

    def failures_to_sql(self):
        tmp_lnk = list()
        for link_ in (self.pipes+self.pumps):
            tmp_lnk.extend(link_.failure)
            link_.failure.clear()
        for index in range(len(tmp_lnk)):
            tmp_lnk[index][1] = tmp_lnk[index][1] / self.timestep

        self.db_handle.insert(tmp_lnk, 'failure', '(link_id, time, type)')
