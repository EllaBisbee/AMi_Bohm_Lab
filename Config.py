"""
Config handles all aspects of the configuration file

Ramon Fernandes, Ella Bisbe
Version 0.0.1
"""

import re
import sys
import os.path
from os import path
import numpy as np

class Config():
    """
    Initializes the configuration options given a configuration file.
    The file must be structured as so:
        nx  ny  samps   # where these are ints as described below
        0.0 0.0 0.0     # where these are floats for tl coords
        0.0 0.0 0.0     # where these are floats for tr coords
        0.0 0.0 0.0     # where these are floats for bl coords
        0.0 0.0 0.0     # where these are floats for br coords
        0.0 0.0         # where these are offsets for each sample (first is always 0. 0.)
        zstep           # where this is a float as described below
        nimages         # where this is an int as described below
        sID             # where this is a string as described below
        nRoot           # where this is a string as described below

    Parameters
    ----------
    fname : path to configuration file

    Attributes
    ----------
    tl         : coords of the top left drop
    tr         : coords of the top right drop
    bl         : coords of the bottom left drop
    br         : coords of the bottom right drop
    nx         : number of well positions along x
    ny         : number of well positions along y
    samps      : number of samples in each well
    zstep      : image spacing in z
    nimages    : number of images per drop
    nroot      : plate name (no spaces)
    sID        : sample name (no spaces)
    filee      : TODO ?????
    alphabet   : TODO ?????
    samp_coord : fractional coordinates of the individual samples
    """
    def __init__(self, fname):
        if fname is None or not os.path.isfile(fname):
            raise ValueError("invalid configuration file path.")

        self.fname = fname
        Ualphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        Lalphabet='abcdefghijklmnopqrstuvwxyz'
        
        try:
            f = open(fname, 'r')
            jnk = list(map(int,(re.findall(r'\S+', (f.readline()).split('#', 1)[0]))))
            self.nx = jnk[0]
            self.ny = jnk[1]
            self.samps = jnk[2]

            self.tl = np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
            self.tr = np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
            self.bl = np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
            self.br = np.array(list(map(float,(re.findall(r'\S+', (f.readline()).split('#', 1)[0])))))
            
            samp_coord = []
            for i in range(self.samps):
                samp_coord.append(list(map(float,(re.findall(r'\S+',f.readline().split('#', 1)[0])))))
            self.samp_coord = samp_coord
            
            self.zstep = float((f.readline()).split('#', 1)[0])
            self.nimages = int((f.readline()).split('#', 1)[0])
            sID = (f.readline()).split('#', 1)[0]
            sID = sID.replace("\n","")
            self.sID = sID.replace(" ","")

            nroot = (f.readline()).split('#', 1)[0]
            nroot = nroot.replace("\n","")
            self.nroot = nroot.replace(" ","")

            self.alphabet=Ualphabet[0:self.ny]+Lalphabet[0:self.ny]
        except:
            f.close()
            raise Exception("invalid file format")
    
    def print_help():
        print(' The format of the configuration file was not right. It should look something like this:')
        print('  12   8    1        # number of positions along x and y and on the plate then number of samples at each position') 
        print('  134.2  29.3  7.5   # coordinates of the top left drop')
        print('   35.2  28.7  7.3   # coordinates of the top right drop')
        print('  133.5  92.9  7.1   # coordinates of the bottom left drop')
        print('   35.0  91.9  7.0   # coordinates of the bottom right drop')
        print('    0.    0.         # offsets for each sample (first sample is always 0. 0.)')
        print('   0.3               # image spacing in z')
        print('   4                 # number of images per drop')
        print('   AMi_sample        # sample name (no spaces)')
        print('   AB_xs2            # plate name (no spaces)')