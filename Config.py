"""Internal representation of the configuration file for AMi

AMi requires external configuration by the user and this file
contains the necessary classes and functions to control the
handling of those files.
"""

import re
import os.path
import string
import numpy as np

class Config():
    """Manages the configuration options specified in the given file

    This class imports, maintains, and exports the configuration specified
    in the given file. The file must be structured as so:
        nx  ny  samps   # Integers as described in attributes
        0.0 0.0 0.0     # Floats for for top-left x,y,z coords
        0.0 0.0 0.0     # Floats for top-right x,y,z coords
        0.0 0.0 0.0     # Floats for bottom-left x,y,z coords
        0.0 0.0 0.0     # Floats for bottom-right x,y,z coords
        0.0 0.0         # Floats for the x,y offsets of each subsample
            Each offset must be on a new line and the first is always 0. 0.
            The number of offsets must match 'samps' specified above
        zstep           # Float as described in attributes
        nimages         # Integer as described in attributes
        sID             # String as described in attributes
        nRoot           # String as described in attributes

    Attributes:
        fname: String path to configuration file
        tl: List of Floats indicating x,y,z coords of the top left drop
        tr: List of Floats indicating x,y,z coords of the top right drop
        bl: List of Floats indicating x,y,z coords of the bottom left drop
        br: List of Floats indicating x,y,z coords of the bottom right drop
        nx: Integer number of well positions along x
        ny: Integer number of well positions along y
        samps: Integer number of samples in each well
        zstep: Float indicating z-change in image spacing between each image
        nimages: Integer number of images per drop
        nroot: String plate name (no spaces)
        sID: String sample name (no spaces)
        samp_coord: fractional coordinates of sub-samples within wells
    """
    def __init__(self, fname):
        """Initializes the configuration based on given file.
        """
        if not os.path.isfile(fname):
            raise ValueError("invalid configuration file path.")

        self.fname = fname
        self._upper_alphabet = string.ascii_uppercase
        self._lower_alphabet = string.ascii_lowercase
        self.read()

    def _next_config(self, file, closure):
        """Retrieves and cleans the next line in the configuration file

        Retrieves the next line from the given file stream.
        Strips comments from the line and considers spaces to designate
        different items. Applies closure to each item.

        Args:
            file: an opened file stream to retrieve the next line from
            closure: function to apply to each item

        Returns:
            A list containing each item after applying closure to them
        """
        line = file.readline()
        line_no_comments = line.split("#", 1)[0]
        items = re.findall(r'\S+', line_no_comments)
        return list(map(closure, items))

    @staticmethod
    def print_help():
        """Static method to print the appropriate format of the file.
        """
        print(' The format of the configuration file was not right. ' +
              'It should look something like this:')
        print(' 12   8    1        # number of positions along x and y and ' +
              'on the plate then number of samples at each position')
        print(' 134.2  29.3  7.5   # coordinates of the top left drop')
        print(' 35.2  28.7  7.3    # coordinates of the top right drop')
        print(' 133.5  92.9  7.1   # coordinates of the bottom left drop')
        print(' 35.0  91.9  7.0    # coordinates of the bottom right drop')
        print(' 0.    0.           # offsets for each sample ' +
              '(first sample is always 0. 0.)')
        print(' 0.3                # image spacing in z')
        print(' 4                  # number of images per drop')
        print(' AMi_sample         # sample name (no spaces)')
        print(' AB_xs2             # plate name (no spaces)')

    @staticmethod
    def write_default_config(fname):
        """Creates a default configuration file

        Args:
            fname: filename to save to
        """
        with open(fname, "w") as f:
            f.write(str('%6d%6d%6d     '%(12, 8, 1) +
                        '# number of positons on x and y, ' +
                        'then the number of samples at each position\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(0., 0., 0.) +
                        '# coordinates of the top left sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(0., 0., 0.) +
                        '# coordinates of the top right sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(0., 0., 0.) +
                        '# coordinates of the bottom left sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(0., 0., 0.) +
                        '# coordinates of the bottom right sample\n'))
            f.write(str('%9.4f%9.4f  '%(0., 0.) +
                        '# fractional offsets of sub-sample \n'))
            f.write(str('%9.3f '%(0.3) +
                        '# zstep - the spacing in z between images\n'))
            f.write(str('%6d     '%(3) +
                        '# nimages - the number of images of each sample\n'))
            f.write('AMi_sample     # sample name\n')
            f.write('AB_xs2         # plate name\n')

    def write(self):
        """Writes to the internal configuration to the stored file name.
        """
        with open(self.fname, "w") as f:
            f.write(str('%6d%6d%6d     '%(self.nx, self.ny, self.samps) +
                        '# number of positons on x and y, then the number of ' +
                        'samples at each position\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(self.tl[0], self.tl[1], self.tl[2])
                        + '# coordinates of the top left sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(self.tr[0], self.tr[1], self.tr[2])
                        + '# coordinates of the top right sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(self.bl[0], self.bl[1], self.bl[2])
                        + '# coordinates of the bottom left sample\n'))
            f.write(str('%9.3f%9.3f%9.3f  '%(self.br[0], self.br[1], self.br[2])
                        + '# coordinates of the bottom right sample\n'))
            self.ensure_samp_coord_dimension()
            for i in range(self.samps):
                x_offset = float(self.samp_coord[i][0])
                y_offset = float(self.samp_coord[i][1])
                f.write(str('%9.4f%9.4f  '%(x_offset, y_offset) +
                            '# fractional offsets of sub-sample \n'))
            f.write(str('%9.3f '%(self.zstep) +
                        '# zstep - the spacing in z between images\n'))
            f.write(str('%6d     '%(self.nimages) +
                        '# nimages - the number of images of each sample\n'))
            f.write(self.sID+'     # sample name\n')
            f.write(self.nroot+'     # plate name\n')

    def read(self):
        """Reads from the stored file name to the internal representation.
        """
        upper_alphabet = self._upper_alphabet
        lower_alphabet = self._lower_alphabet

        try:
            with open(self.fname, 'r') as f:
                self.nx, self.ny, self.samps = self._next_config(f, int)
                self.tl = np.array(self._next_config(f, float))
                self.tr = np.array(self._next_config(f, float))
                self.bl = np.array(self._next_config(f, float))
                self.br = np.array(self._next_config(f, float))
                self.samp_coord = [
                    self._next_config(f, float) for _ in range(self.samps)]
                self.zstep = self._next_config(f, float)[0]
                self.nimages = self._next_config(f, int)[0]
                self.sID = self._next_config(
                    f, str)[0].replace("\n", "").replace(" ", "")
                self.nroot = self._next_config(
                    f, str)[0].replace("\n", "").replace(" ", "")
                self._alphabet = (upper_alphabet[0:self.ny] +
                                  lower_alphabet[0:self.ny])
        except:
            raise Exception("invalid file format")

    def ensure_samp_coord_dimension(self):
        """Ensures that samp_coord attribute has as the correct dimension.

        len(self.samp_coord) == samps
        """
        if len(self.samp_coord) < self.samps:
            diff = self.samps - len(self.samp_coord)
            self.samp_coord.extend([[0., 0.] for _ in range(diff)])

    def get_subsample_id(self, samp):
        """Returns the subsample name given the subsample index.

        Returns a lowercase letter representing the subsample name

        Args:
            samp: An integer representing the subsample within a well
        """
        return self._lower_alphabet[samp]

    def get_subsample_index(self, letter):
        """Returns the subsample index given the subsample letter.

        Returns an integer representing the subsample within a well.
        This is the inverse of get_subsample_id, ex:
            get_subsample_index(get_subsample_id(0)) == 0

        Args:
            letter: A single letter representing the subsample

        Throws:
            Exception if given letter is out of bounds
        """
        if letter in self._upper_alphabet[0:self.samps]:
            return self._upper_alphabet.find(letter)
        elif letter in self._lower_alphabet[0:self.samps]:
            return self._lower_alphabet.find(letter)
        else:
            raise Exception("invalid subsample identification")

    def get_sample_name(self, row, col):
        """Returns the sample name (excluding subsample).

        Returns the external sample name given a row and column. This
        does not include the subsample, only the major well name (e.g. A1)

        Args:
            row: An integer for the well's row number
            col: An integer for the well's column number
        """
        return self._alphabet[row] + str(col + 1)

    def get_row_col(self, name):
        """Returns the row and column indices of a given sample name

        Sample name must be an integer or in letter_number format
        E.g. 5 or A1

        Args:
            name: the sample name

        Throws:
            Exception if name is invalid
        """
        if name[0].isdigit(): # name is in integer format
            numb = int(name)
            numb -= 1
            assert numb < self.nx * self.ny and numb >= 0
            row = int(numb / self.nx)
            col = numb - (row * self.nx)
            return row, col
        else: # name is in letter_number format
            rowletter = name[0].upper()
            colnum = int(name[1:])
            row = self._alphabet.index(rowletter)
            col = colnum - 1
            return row, col

    def get_name_with_subsample(self, row, col, samp):
        """Returns the sample name with the subsample id

        Args:
            row: An integer for the well's row number
            col: An integer for the well's column number
            samp: An integer for the subsample index
        """
        return self.get_sample_name(row, col) + self.get_subsample_id(samp)

    def is_valid_sample_name(self, name):
        """Checks if the given name is a valid sample name in format
        LETTER then NUMBER (e.g. A1, B4)

        Args:
            name: the sample name
        """
        rowletter = name[0]
        colnum = int(name[1:])

        return rowletter in self._alphabet and colnum <= self.nx
