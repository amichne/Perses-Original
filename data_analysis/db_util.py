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

    def failure_type(self, type_):
        exec_str = '''
                    SELECT (time) FROM {}.failure
                    WHERE type = \'{}\'
                    '''.format(self.db, type_.value)
        self.cursor.execute(exec_str)
        return list(set([x[0] for x in self.cursor.fetchall()]))
        # return self.cursor.fetchall()

    def all_failure(self):
        exec_str = '''
                    SELECT * FROM {}.failure
                    ORDER BY time ASC
                    '''.format(self.db)
        self.cursor.execute(exec_str)
        return list(set([x for x in self.cursor.fetchall()]))
