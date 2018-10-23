from controller import Controller

cont = Controller('../data/epanet2.dll')
cont.load_network('../data/north_marin_c.inp', 'tmp.txt')
cont.populate()
