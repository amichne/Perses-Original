from dataclasses import dataclass
from typing import List


class Pump:
    electronic_failure_state = False
    motor_failure_state = False
    electronic_repair_time: int
    motor_repair_time: int
    failure_events: List[int] = list()

    def failure(self):
        print()


class Pipe:
    id_: str
    term_node_a: str
    term_node_b: str
    failure_state: bool = False
    emit_coeff_a: float
    emit_coeff_b: float
