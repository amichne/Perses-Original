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
            user=user, password=password, db='example', host=host)
        self.cursor = self.connection.cursor()
        self.user = user
        self.host = host
        self.db = db

    def reset_db(self):
        try:
            exec_str = "SELECT 'DROP TABLE \"' || TABLE_NAME || '\" CASCADE CONSTRAINTS;' from {}".format(
                self.db)
            self.cursor.execute(exec_str)
            self.connection.commit()
        except Exception:
            pass

        try:
            exec_str = '''
                    DROP DATABASE
                    IF EXISTS {}
                    '''.format(self.db)
            self.cursor.execute(exec_str)
            self.connection.commit()
        except Exception:
            pass
        exec_str = '''CREATE DATABASE {}'''.format(self.db)
        self.cursor.execute(exec_str)
        self.connection.commit()

    def create_table(self, table, schema):
        exec_str = '''CREATE TABLE {0}.{1} {2}'''.format(
            self.db, table, schema)
        self.cursor.execute(exec_str)
        self.connection.commit()

    def insert(self, rows, table, columns):
        exec_str = '''
                    INSERT INTO {0}.{1}
                    {2}
                    values (%s, %s, %s)
                   '''.format(self.db, table, columns)
        self.cursor.executemany(exec_str, rows)
        self.connection.commit()

    def create_index(self, table, index_name, columns):
        exec_str = '''
                    CREATE INDEX {0}
                    ON {1}.{2} ({3})
                   '''.format(index_name, self.db, table, *columns)
        self.cursor.execute(exec_str)
        self.connection.commit()
