"""
Microscope handles all aspects of external interactions with the microscope unit

Ramon Fernandes, Ella Bisbe
Version 0.0.2
"""

class Microscope():
    """
    CLASS DESCRIPTION HERE

    Parameters
    ----------
    

    Attributes
    ----------
    xcol    : Sample position (x)
    yrow    : Sample position (y)
    samp    : Sub-sample index (used when there is more than one sample in each well)
    mx      : Machine position (x)
    my      : Machine position (y)
    mz      : Machine position (z)
    """
    def __init__(self):
        self.xcol = 0
        self.yrow = 0
        self.samp = 0
        self.mx = 0
        self.my = 0
        self.mz = 0

    def get_machine_position(self):
        return [self.mx, self.my, self.mz]

    def mcoords(self):
        print("Moving to cell")