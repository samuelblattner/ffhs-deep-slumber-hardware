from enum import Enum


class OrchestraState(Enum):

    IDLE = 1
    READY = 2
    RECORDING = 3
    PAUSED = 4
