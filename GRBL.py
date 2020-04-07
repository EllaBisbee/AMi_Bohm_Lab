"""A GRBL interface to interact with the CNC Machine

A GRBL Interface to abstractly interact with the CNC Machine
This is currently not an all-encompassing GRBL interface and includes
methods necessary for the interactions needed for this program in particular.
It is based on information gathered from the following guides and sources:
http://www.diymachining.com/downloads/GRBL_Settings_Pocket_Guide_Rev_B.pdf
https://diymachining.com/grbl-settings-101-a-how-to-guide/
https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface

As noted in the URLs above, this interface is based on GRBL v1.1
"""

# Real-Time Commands
CYCLE_START = "~"
FEED_HOLD = "!"
CURRENT_STATUS = "?"

# $x Settings Messages
COMMAND_PREFIX = "$"
VIEW_SETTINGS = "$$"
STEP_PULSE_TIME = 0
STEP_IDLE_DELAY = 1
STEP_PULSE_CONFIG = 2
AXIS_DIRECTION = 3
STEP_ENABLE_INVERT = 4
LIMIT_PINS_INVERT = 5
PROBE_PIN_INVERT = 6
STATUS_REPORT = 10
JUNCTION_DEVIATION = 11
ARC_TOLERANCE = 12
FEEDBACK_UNITS = 13
SOFT_LIMITS = 20
HARD_LIMITS = 21
HOMING_CYCLE = 22
HOMING_CYCLE_DIRECTION = 23
HOMING_FEED = 24
HOMING_SEEK = 25
HOMING_DEBOUNCE = 26
HOMING_PULL_OFF = 27
MAX_SPINDLE = 30
MIN_SPINGLE = 31
LASER_MODE = 32
X_STEPS = 100
Y_STEPS = 101
Z_STEPS = 102
X_MAX_RATE = 110
Y_MAX_RATE = 111
Z_MAX_RATE = 112
X_ACCELERATION = 120
Y_ACCELERATION = 121
Z_ACCELERATION = 122
X_MAX_TRAVEL = 130
Y_MAX_TRAVEL = 131
Z_MAX_TRAVEL = 132

class GRBL():
    """TODO: SHORT DESCRIPTION HERE

    TODO: LONGER DESCRIPTION HERE

    Attributes:
        
    """