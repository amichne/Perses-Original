import MySQLdb as sql
import MySQLdb.connections as connections

from getpass import getpass


class DatabaseHandle:
    connection = connections.Connection
    cursor = connections.cursors.Cursor
    user = None
    host = None
    db = None

    def __init__(self, user, password, db, host):
        self.connection = sql.connect(
            user=user, password=password, db=db, host=host)
        self.cursor = self.connection.cursor()
        self.user = user
        self.host = host
        self.db = db

    def convert(self, data, index, coeff):
        for i in range(len(data)):
            data[i] = list(data[i])
            data[i][index] = data[i][index] * coeff
        return data

    def failure_type(self, type_, coeff=1):
        exec_str = '''
                    SELECT time, link_id FROM {}.failure
                    WHERE type = \'{}\'
                    '''.format(self.db, type_)
        self.cursor.execute(exec_str)
        return [x for x in self.convert(list(set(self.cursor.fetchall())), 0, 60*60)]
        # return self.cursor.fetchall()

    def get_nodes(self):
        exec_str = '''
                    SELECT DISTINCT node_id from {}.pressure
                    '''.format(self.db)

        self.cursor.execute(exec_str)
        return list(self.cursor.fetchall())

    def sub_threshold(self, node_id, threshold):
        exec_str = '''
                    SELECT
                        COUNT(node_id)
                    FROM {0}.pressure
                    WHERE pressure < {1}
                    '''.format(self.db, threshold)
        self.cursor.execute(exec_str)
        return int(self.cursor.fetchall()[0])

    def outage_by_time(self, threshold):
        exec_str = '''
                    SELECT node_id, time
                    FROM {0}.pressure
                    WHERE pressure < {1}
                    '''.format(self.db, threshold)
        self.cursor.execute(exec_str)
        return self.convert(list(self.cursor.fetchall()), 1, 60*60)

    def drop_self(self):
        exec_str = '''
                    DROP database {0}
                    '''.format(self.db)
        self.cursor.execute(exec_str)
        self.connection.commit()

    def drop_tables(self, exclude=[]):
        for table in (set(('pressure', 'failure')) - set(exclude)):
            exec_str = '''
                        DROP table {0}.{1}
                        '''.format(self.db, table)
            self.cursor.execute(exec_str)
            self.connection.commit()


def database_loader(db_params):
    if isinstance(db_params, dict):
        db = DatabaseHandle(**db_params)
        return db
    elif isinstance(db_params, DatabaseHandle):
        return db_params
    else:
        raise Exception('db_params must be dict or DatabaseHandle')
