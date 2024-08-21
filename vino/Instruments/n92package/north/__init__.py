

# ?: bool
# i: int
# B: unsigned byte
# f: float
STEP_HEADER_FMT = 'i??iBii' # full format includes: + 'f' * N_AXES  when N_AXES is defined by project

import logging
from enum import Enum

SimMateSignal = Enum('SimMateSignal', ['NONE', 'OUTPUT_LOW', 'OUTPUT_HIGH', 'UNCAP', 'CAP'])

def dist(p, q):
     import math
     return math.sqrt(sum((px - qx) ** 2.0 for px, qx in zip(p, q)))


# imports last to avoid cyclical importing (some of the below files depend on the constants above)
import north.n9_kinematics
from north.north_c9 import NorthC9, ADS1115
from north.north_tasks import Scheduler
from north.n9_cam import NorthCamera
from north.n9_data import NorthData
