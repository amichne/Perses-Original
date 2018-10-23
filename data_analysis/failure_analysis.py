from getpass import getpass

from db_util import DatabaseHandle


pass__ = getpass()
params = {'user': 'root', 'db': 'example',
          'host': 'localhost', 'password': pass__}

db = DatabaseHandle(**params)
elec_failures = db.comp_failure('10', 2)
motor_failures = db.comp_failure('10', 3)

print(len(elec_failures))
print(len(list(set(elec_failures))))

print(len(motor_failures))
print(len(list(set(motor_failures))))
