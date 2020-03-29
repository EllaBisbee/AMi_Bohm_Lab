"""
Config handles all aspects of the configuration file

Ramon Fernandes, Ella Bisbe
Version 0.0.2
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
    fname      : path to configuration file
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
    alphabet   : used to keep track of labels for wells
    Ualphabet  : Used to track main wells
    Lalphabet  : Used to track sub-samples within each well
    samp_coord : fractional coordinates of the individual samples
    """
    def __init__(self, fname):
        if fname is None or not os.path.isfile(fname):
            raise ValueError("invalid configuration file path.")

        self.fname = fname
        self.Ualphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.Lalphabet = 'abcdefghijklmnopqrstuvwxyz'
        self.read()
    
    """
    Retrieves the next line from the given file stream.
    Strips comments from the line and applies f to each item on the line
    Returns a list containing the mapped items.

    Parameters
    ----------
    file : an opened file stream
    f    : function to apply to each item
    """
    def _next_config(self, file, f):
        line = file.readline()
        line_no_comments = line.split("#", 1)[0]
        items = re.findall(r'\S+', line_no_comments)
        return list(map(f, items))
    
    @staticmethod
    def print_help():
        print(' The format of the configuration file was not right. It should look something like this:')
        print(' 12   8    1        # number of positions along x and y and on the plate then number of samples at each position') 
        print(' 134.2  29.3  7.5   # coordinates of the top left drop')
        print(' 35.2  28.7  7.3    # coordinates of the top right drop')
        print(' 133.5  92.9  7.1   # coordinates of the bottom left drop')
        print(' 35.0  91.9  7.0    # coordinates of the bottom right drop')
        print(' 0.    0.           # offsets for each sample (first sample is always 0. 0.)')
        print(' 0.3                # image spacing in z')
        print(' 4                  # number of images per drop')
        print(' AMi_sample         # sample name (no spaces)')
        print(' AB_xs2             # plate name (no spaces)')

    def write(self):
        with open(self.fname, "w") as f:
            f.write(str('%6d%6d%6d     # number of positons on x and y, then the number of samples at each position\n'%(self.nx,self.ny,self.samps)))
            f.write(str('%9.3f%9.3f%9.3f  # coordinates of the top left sample\n'%(self.tl[0],self.tl[1],self.tl[2])))
            f.write(str('%9.3f%9.3f%9.3f  # coordinates of the top right sample\n'%(self.tr[0],self.tr[1],self.tr[2])))
            f.write(str('%9.3f%9.3f%9.3f  # coordinates of the bottom left sample\n'%(self.bl[0],self.bl[1],self.bl[2])))
            f.write(str('%9.3f%9.3f%9.3f  # coordinates of the bottom right sample\n'%(self.br[0],self.br[1],self.br[2])))
            for i in range(self.samps):
                try: 
                    test=self.samp_coord[i]
                except: 
                    self.samp_coord.append([0., 0.])
                ta=float(self.samp_coord[i][0])
                tb=float(self.samp_coord[i][1])
                f.write(str('%9.4f%9.4f  # fractional offsets of sub-sample \n'%(ta,tb)))
            f.write(str('%9.3f # zstep - the spacing in z between images\n'%(self.zstep)))
            f.write(str('%6d     # nimages - the number of images of each sample\n'%(self.nimages)))
            f.write(self.sID+'     # sample name\n')
            f.write(self.nroot+'     # plate name\n')

    def read(self):
        Ualphabet=self.Ualphabet
        Lalphabet=self.Lalphabet

        try:
            with open(self.fname, 'r') as f:
                self.nx, self.ny, self.samps = self._next_config(f, int)
                self.tl = np.array(self._next_config(f, float))
                self.tr = np.array(self._next_config(f, float))
                self.bl = np.array(self._next_config(f, float))
                self.br = np.array(self._next_config(f, float))
                self.samp_coord = [self._next_config(f, float) for _ in range(self.samps)]
                self.zstep = self._next_config(f, float)[0]
                self.nimages = self._next_config(f, int)[0]
                self.sID = self._next_config(f, str)[0].replace("\n", "").replace(" ", "")
                self.nroot = self._next_config(f, str)[0].replace("\n", "").replace(" ", "")
                self.alphabet=Ualphabet[0:self.ny]+Lalphabet[0:self.ny]
        except:
            raise Exception("invalid file format")

    """
    Get the sub-sample letter id given sub-sample index
    """
    def get_subsample_id(self, samp):
        return self.Lalphabet[samp]

    """
    Get the sub-sample index given the sub-sample letter
    """
    def get_subsample_index(self, letter):
        if letter in self.Ualphabet[0:self.samps]:
            return self.Ualphabet.find(letter)
        else:
            return self.Lalphabet.find(letter)

    """
    Get the sample name given row and column
    """
    def get_sample_name(self, row, col):
        return self.alphabet[row] + str(col + 1)