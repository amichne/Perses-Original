import dask.delayed

from hydraulic_simulation.components import LinkType


def threaded_eval(pipe, temp, simtime):
    '''
    Evaluate exposure progression for TAS Max and Simtime:
        temp: float of tasmax in deg C
        simtime: int for current time of simulation in seconds'''
    pipe.exp, pipe.status = pipe.progression(
        pipe.exp, pipe.status, temp, simtime, pipe.type_)
    return pipe


def threaded_bimodal_eval(pump, temp, simtime):
    pump.exp_elec, pump.status_elec = pump.progression(
        pump.exp_elec, pump.status_elec, temp, simtime, LinkType('elec'))
    pump.exp_motor, pump.status_motor = pump.progression(
        pump.exp_motor, pump.status_motor, temp, simtime, LinkType('motor'))
    return pump


@dask.delayed
def chunked_pipes(pipes, temp, time):
    return [threaded_eval(pipe, temp, time) for pipe in pipes]


@dask.delayed
def chunked_pumps(pumps, temp, time):
    return [threaded_bimodal_eval(pump, temp, time) for pump in pumps]
