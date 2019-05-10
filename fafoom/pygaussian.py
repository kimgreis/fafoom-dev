'''Wrapper for Gaussian'''

from __future__ import division
import glob
import os
import subprocess

from utilities import sdf2gjf

hartree2eV = 27.21138602

class GaussianObject():
    '''Create and handle Gaussian objects.'''
    def __init__(self, commandline, memory, fafoompath, name_inputfile="gaussian_molecule", chargemult="1 1", nprocs=32):
        """Initialize the GaussianObject.

        Args(required): 
            commandline
            memory
            fafoompath
        Args(optional):
            chargemult (default="1 1")
            nprocs (default=32)
        Raises:
            KeyError: if the commandline, memory or fafoompath is not defined
        """
        self.commandline = commandline
        self.name_inputfile = name_inputfile
        self.memory = memory
        self.chargemult = chargemult
        self.nprocs = nprocs
        self.fafoompath = fafoompath

    def generate_input(self, sdf_string):
        """Create input files for Gaussian.
        Args:
            sdf_string (str)
        """
        gjf_string = sdf2gjf(sdf_string)
        coord = gjf_string.split('\n')
        string1 = '%chk='+str(self.name_inputfile)+'\n'
        string2 = '%mem='+str(self.memory)+'\n'
        string3 = '%nprocs='+str(self.nprocs)+'\n'
        string4 = '# ' +str(self.commandline)+'\n'
        string5 = '\n'
        string6 = str(self.name_inputfile)+'\n'
        string7 = '\n'
        string8 = str(self.chargemult)+'\n'
        with open('gaussian_molecule.gjf', 'w') as f:
            f.write(string1)
            f.write(string2)
            f.write(string3)
            f.write(string4)
            f.write(string5)
            f.write(string6)
            f.write(string7)
            f.write(string8)
            f.write('\n'.join(coord))
            
    def run_gaussian(self, execution_string):
        """Run Gaussian (will automatically write output to 'gaussian_molecule.log').
        After each run the content of the 'gaussian_molecule.log is appened to 'results.out'.
        The optimized geometry is written to 'gaussian_molecule.xyz'.

        Warning: this function uses subprocessing to invoke the run.
        The subprocess's shell is set to TRUE.
        Args:
            execution_string (str): e.g. Gaussian or for parallel version
            /the/complete/path/to/gaussian
        Raises:
            OSError: if gaussian_molecule.gjf not present in the working directory
        """
        success = False
        if os.path.exists('gaussian_molecule.gjf') is False:
            raise OSError("Required input file not present.")
        gaussian = subprocess.Popen(
            execution_string+str(" gaussian_molecule.gjf"),
            stdout=subprocess.PIPE, shell=True)
        gaussian.wait()

        datafile = open("gaussian_molecule.log", "r")
        data = datafile.read()
        datafile.close()

        results = open("results.out", "a")
        results.write(data)
        results.close()

        searchfile = open("gaussian_molecule.log", "r")

        s0 = "Normal termination of Gaussian"
        s = "SCF Done"
        not_conv = True
        for line in searchfile:
            if s0 in line:
                not_conv = False
        searchfile.close()
        if not_conv:
            killfile = open("kill.dat", "w")
            killfile.close()
        else:
            searchfile = open("gaussian_molecule.log", "r")
            for line in searchfile:
                if s in line:
                    energy_tmp = float(line.split(" ")[7])
            searchfile.close()
            self.energy = energy_tmp

            os.system('python ' + str(self.fafoompath) + '/get_geometry_gaussian.py gaussian_molecule.log')
    
            with open('gaussian_molecule.xyz', 'r') as f:
                self.xyz_string_opt = f.read()
            f.close()
            success = True
        return success          

    def get_energy(self):
        """Get the energy of the molecule.

        Returns:
            energy (float) in eV
        Raises:
            AttributeError: if energy hasn't been calculated yet
        """
        if not hasattr(self, 'energy'):
            raise AttributeError("The calculation wasn't performed yet.")
        else:
            return hartree2eV*self.energy

    def get_xyz_string_opt(self):
        """Get the optimized xyz string.

        Returns:
            optimized xyz string (str)
        Raises:
            AttributeError: if the optimization hasn't been performed yet
        """
        if not hasattr(self, 'xyz_string_opt'):
            raise AttributeError("The calculation wasn't performed yet.")
        else:
            return self.xyz_string_opt

    def clean(self):
        """Clean the working direction after the gaussian calculation has been
        completed.
        """
        for f in glob.glob("gaussian_molecule.*"):
            os.remove(f)
