#    Copyright 2015 Adriana Supady
#
#    This file is part of fafoom.
#
#   Fafoom is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   Fafoom is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#   along with fafoom.  If not, see <http://www.gnu.org/licenses/>.
''' Handle the degrees of freedom.'''
from __future__ import division
import math
from copy import copy
from random import choice
from rdkit import Chem

from utilities import ig, cleaner, get_vec, tor_rmsd, find_one_in_list
from measure import *

from genetic_operations import mutation

from rdkit import Chem
from rdkit.Chem import AllChem

from operator import itemgetter
from rdkit.Chem import rdMolTransforms
from utilities import *
import numpy as np

class DOF:

    def __init__(self, name):
        self.name = name

    def common_function():
        pass

class Orientation(DOF):
    '''Find and handle orientation of the molecule. '''
    
    values_options = [range(0, 91, 90), np.arange(0, 2, 1)] #values_options[0] - Defines angle, values_options[1] - defines orientaion.

    @staticmethod
    def find(smiles, positions=None):
        if positions is None:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("The smiles is invalid")
            pattern_cent = Chem.MolFromSmarts(smiles)
            cent = list(mol.GetSubstructMatches(pattern_cent))
            positions = cleaner(cent)
        return positions #returns all atoms

    def __init__(self, positions):
        """Initialaize the Centroid object from the positions."""
        self.name = 'Orientation'        
        self.type = "orientation"
        self.positions = positions

    def apply_on_string(self, string, values_to_set=None):
        mol = Chem.MolFromMolBlock(string, removeHs=False)
        atom_1_indx = 0
        atom_2_indx = mol.GetNumHeavyAtoms() - 1   
        if values_to_set is not None:
            self.values = np.array(values_to_set)
        string = quaternion_set(string, self.values, atom_1_indx, atom_2_indx)
        return string

    def get_random_values(self):
        """Generate a random value for orientation of the molecule. Random orientation defined with direction vector and angle"""
        self.values = np.array([choice(Orientation.values_options[0]),
                                choice(Orientation.values_options[1]),
                                choice(Orientation.values_options[1]),
                                choice(Orientation.values_options[1])])  
        if np.linalg.norm(np.array(self.values[1:])) == 0:
            self.values = np.array([self.values[0], 0.0, 0.00001, 0.99999])
        if self.values[1] == 0 and self.values[2] == 0 and self.values[3] == 1:
            self.values = np.array([self.values[0], 0.0, 0.00001, 0.99999])
        if self.values[1] == 0 and self.values[2] == 0 and self.values[3] == -1:
            self.values = np.array([self.values[0], 0.0, -0.00001, -0.99999])


    def update_values(self, string):
        mol = Chem.MolFromMolBlock(string, removeHs=False)
        atom_1_indx = 0
        atom_2_indx = mol.GetNumHeavyAtoms() - 1
        self.values = quaternion_measure(string, atom_1_indx, atom_2_indx)


#### NEEEED to be deeply revised...

    def get_weighted_values(self, weights):
        if len(weights) == len(Orientation.values_options):
            self.values = [Orientation.values_options[find_one_in_list(sum(
                           weights), weights)]
                           for i in range(len(self.positions))]
        else:
            self.values = np.array([choice(Orientation.values_options)
                           for i in range(len(self.positions))])        

    def mutate_values(self, max_mutations=None, weights=None):

        if max_mutations is None:
            max_mutations = max(1, int(math.ceil(len(self.values)/2.0)))
        values_to_mutate = range(2,10, 1)
        self.values = mutation(self.values, max_mutations,
                               values_to_mutate, weights, periodic=False)
        #~ self.values = mutation(self.values, max_mutations,
                               #~ Orientation.values_options, weights, periodic=False)

    def is_equal(self, other, threshold, chiral=True):
        threshold = 45
        values = []
        angle_between(self.values[1:], other.values[1:])
        values.append(angle_between(self.values[1:], other.values[1:]))
        if hasattr(other, "initial_values"):
            values.append(angle_between(self.values[1:], other.values[1:]))
        if min(values) > threshold:
            return False
        else:
            return True
                             
class Centroid(DOF):
    '''Find and handle centre of the molecule. '''
    values_options = [range(0,1,1), range(0, 1, 1), range(6, 10, 1)]

    @staticmethod
    def find(smiles, positions=None):
        if positions is None:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("The smiles is invalid")
            pattern_cent = Chem.MolFromSmarts(smiles)
            cent = list(mol.GetSubstructMatches(pattern_cent))
            positions = cleaner(cent)
        return positions #returns all atoms

    def __init__(self, positions):
        """Initialaize the Centroid object from the positions."""
        self.name = 'Centroid'        
        self.type = "centroid"
        self.positions = positions

    def apply_on_string(self, string, values_to_set=None):
        if values_to_set is not None:
            self.values = np.array(values_to_set)
        string = centroid_set(string, self.values)
        return string

    def get_random_values(self):
        """Generate a random value for position of the Centroid object"""
        self.values = np.array([choice(Centroid.values_options[0]), choice(Centroid.values_options[1]), choice(Centroid.values_options[2])])


    def update_values(self, string):
        self.values = centroid_measure(string)
        
#### NEEEED to be deeply revised...
    def get_weighted_values(self, weights):
        if len(weights) == len(Centroid.values_options):
            self.values = [Centroid.values_options[find_one_in_list(sum(
                           weights), weights)]
                           for i in range(len(self.positions))]
        else:
            self.values = np.array([choice(Centroid.values_options)
                           for i in range(len(self.positions))])        

    def mutate_values(self, max_mutations=None, weights=None):

        if max_mutations is None:
            max_mutations = max(1, int(math.ceil(len(self.values)/2.0)))
        values_to_mutate = range(2, 5, 1)
        self.values = mutation(self.values, max_mutations,
                               values_to_mutate, weights, periodic=False)
        #~ self.values = mutation(self.values, max_mutations,
                               #~ Centroid.values_options, weights, periodic=False)

    def is_equal(self, other, threshold, chiral=True):
        threshold = 1
        values = []
        values.append(np.linalg.norm(np.array(self.values) - np.array(other.values)))
        if hasattr(other, "initial_values"):
            values.append(np.linalg.norm(np.array(self.values) - np.array(other.values)))
        if min(values) > threshold:
            return False
        else:
            return True

class Torsion(DOF):
    """ Find, create and handle rotatable bonds"""
    # Rotatable Bonds can freely rotate around themselves
    values_options = range(-179, 181, 1)

    @staticmethod
    def find(smiles, smarts_torsion="[*]~[!$(*#*)&!D1]-&!@[!$(*#*)&!D1]~[*]",
             filter_smarts_torsion=None, positions=None):
        """Find the positions of rotatable bonds in the molecule.

        Args(required):
            smiles (str)
        Arge(optional)
            smarts_torion (str) : pattern defintion for the torsions, if not
            defined, a default pattern "[*]~[!$(*#*)&!D1]-&!@[!$(*#*)&!D1]~[*]"
            will be used
            filter_smarts_torsion (str): pattern defition for the torsion to be
            ignored
            positions (list of tuples) : if the positions (in terms of atom
            indicies) of the torsions is known, they can be passed directly
        """
        if positions is None:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("The smiles is invalid")
            pattern_tor = Chem.MolFromSmarts(smarts_torsion)
            torsion = list(mol.GetSubstructMatches(pattern_tor))

            if filter_smarts_torsion:
                pattern_custom = Chem.MolFromSmarts(filter_smarts_torsion)
                custom = list(mol.GetSubstructMatches(pattern_custom))
                to_del_bef_custom = []

                for x in reversed(range(len(torsion))):
                    for y in reversed(range(len(custom))):
                        ix1, ix2 = ig(1)(torsion[x]), ig(2)(torsion[x])
                        iy1, iy2 = ig(1)(custom[y]), ig(2)(custom[y])
                        if (ix1 == iy1 and ix2 == iy2) or (ix1 == iy2 and
                                                           ix2 == iy1):
                            to_del_bef_custom.append(x)

                custom_torsion = copy(torsion)
                custom_torsion = [v for i, v in enumerate(custom_torsion)
                                  if i not in set(to_del_bef_custom)]
                torsion = custom_torsion

            positions = cleaner(torsion)

        return positions

    def __init__(self, positions):
        """Initialaize the Torsion object from the positions."""
        self.name = 'Torsion'
        self.type = "torsion"
        self.positions = positions

    def get_random_values(self):
        """Generate a random value for each of the positions of the Torsion
        object"""
        self.values = [choice(Torsion.values_options)
                       for i in range(len(self.positions))]

    def get_weighted_values(self, weights):
        """Generate a random, but weighted value for each of the positions of
        the Torsion object.

        Args:
            weights (list): weights for all allowed values options, if it is
            not of the length of the values options, random values will be
            generated
        """
        if len(weights) == len(Torsion.values_options):
            self.values = [Torsion.values_options[find_one_in_list(sum(
                           weights), weights)]
                           for i in range(len(self.positions))]
        else:
            self.values = [choice(Torsion.values_options)
                           for i in range(len(self.positions))]

    def apply_on_string(self, string, values_to_set=None):
        """Adjust the sdf string to match the values of the Torsion object.

        Args(required):
            sdf_string
        Args(optional):
            values_to_set (list) : a list of values to be set can be passed
            directly
        """
        if values_to_set is not None:
            self.values = values_to_set
        for i in range(len(self.positions)):
            string = dihedral_set(string, self.positions[i],
                                  self.values[i])
        return string

    def mutate_values(self, max_mutations=None, weights=None):
        """Call for a mutation of the list of Torsion object values

        Args (optional):
            max_mutations (int): maximal number of mutations to be performed on
            the values list
            weights (list) : weights for the values_options
        """
        if max_mutations is None:
            max_mutations = max(1, int(math.ceil(len(self.values)/2.0)))
        self.values = mutation(self.values, max_mutations,
                               Torsion.values_options, weights, periodic=True)

    def update_values(self, string):
        """Measure and update the Torsion object values.

        Args:
            sdf_string
        """
        updated_values = []
        for i in range(len(self.positions)):
            updated_values.append(dihedral_measure(string,
                                                   self.positions[i]))
        self.values = updated_values

    def is_equal(self, other, threshold, chiral=True):
        """Decide if the values of two Torsion objects are equal or not
        (based on Torsional RMSD). If the objects have the "initial_values"
        attributes, they will be taken into account too.

        Args(optional):
            chiral (bool): default-True, if set to False, mirror image of the
            structure will be considered too
        """

        values = []
        values.append(tor_rmsd(2, get_vec(self.values, other.values)))

        if hasattr(other, "initial_values"):
            values.append(tor_rmsd(2, get_vec(self.values,
                                              other.initial_values)))
        if not chiral:
            values.append(tor_rmsd(2, get_vec(self.values,
                                              [-1*i for i in other.values])))
            if hasattr(other, "initial_values"):
                values.append(tor_rmsd(2, get_vec(self.values, [-1*i for i in
                                                  other.initial_values])))
        if min(values) > threshold:
            return False
        else:
            return True


class PyranoseRing(DOF):

    # 0,1: chairs; 2-7:boats; 8-13:skewboats; 14-25:halfchairs; 26-37:envelopes
    dict_for_ring_dih = {'0': [60.0, -60.0, 60.0, -60.0, 60.0, -60.0],
                         '1': [-60.0, 60.0, -60.0, 60.0, -60.0, 60.0],
                         '2': [0.0, 60.0, -60.0, 0.0, 60.0, -60.0],
                         '3': [60.0, 0.0, -60.0, 60.0, 0.0, -60.0],
                         '4': [60.0, -60.0, 0.0, 60.0, -60.0, 0.0],
                         '5': [0.0, -60.0, 60.0, 0.0, -60.0, 60.0],
                         '6': [-60.0, 0.0, 60.0, -60.0, 0.0, 60.0],
                         '7': [-60.0, 60.0, 0.0, -60.0, 60.0, 0.0],
                         '8': [30.0, 30.0, -60.0, 30.0, 30.0, -60.0],
                         '9': [60.0, -30.0, -30.0, 60.0, -30.0, -30.0],
                         '10': [30.0, -60.0, 30.0, 30.0, -60.0, 30.0],
                         '11': [-30.0, -30.0, 60.0, -30.0, -30.0, 60.0],
                         '12': [-60.0, 30.0, 30.0, -60.0, 30.0, 30.0],
                         '13': [-30.0, 60.0, -30.0, -30.0, 60.0, -30.0],
                         '14': [45.0, -15.0, 0.0, -15.0, 45.0, -60.0],
                         '15': [60.0, -45.0, 15.0, 0.0, 15.0, -45.0],
                         '16': [45.0, -60.0, 45.0, -15.0, 0.0, -15.0],
                         '17': [15.0, -45.0, 60.0, -45.0, 15.0, 0.0],
                         '18': [0.0, -15.0, 45.0, -60.0, 45.0, -15.0],
                         '19': [15.0, 0.0, 15.0, -45.0, 60.0, -45.0],
                         '20': [-15.0, 45.0, -60.0, 45.0, -15.0, 0.0],
                         '21': [0.0, 15.0, -45.0, 60.0, -45.0, 15.0],
                         '22': [-15.0, 0.0, -15.0, 45.0, -60.0, 45.0],
                         '23': [-45.0, 15.0, 0.0, 15.0, -45.0, 60.0],
                         '24': [-60.0, 45.0, -15.0, 0.0, -15.0, 45.0],
                         '25': [-45.0, 60.0, -45.0, 15.0, 0.0, 15.0],
                         '26': [30.0, 0.0, 0.0, -30.0, 60.0, -60.0],
                         '27': [60.0, -30.0, 0.0, 0.0, 30.0, -60.0],
                         '28': [60.0, -60.0, 30.0, 0.0, 0.0, -30.0],
                         '29': [30.0, -60.0, 60.0, -30.0, 0.0, 0.0],
                         '30': [0.0, -30.0, 60.0, -60.0, 30.0, 0.0],
                         '31': [0.0, 0.0, 30.0, -60.0, 60.0, -30.0],
                         '32': [-30.0, 60.0, -60.0, 30.0, 0.0, 0.0],
                         '33': [0.0, 30.0, -60.0, 60.0, -30.0, 0.0],
                         '34': [0.0, 0.0, -30.0, 60.0, -60.0, 30.0],
                         '35': [-30.0, 0.0, 0.0, 30.0, -60.0, 60.0],
                         '36': [-60.0, 30.0, 0.0, 0.0, -30.0, 60.0],
                         '37': [-60.0, 60.0, -30.0, 0.0, 0.0, 30.0]}

    dict_for_ring_ang = {'0': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '1': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '2': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '3': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '4': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '5': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '6': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '7': [109.5, 109.5, 109.5, 109.5, 109.5],
                         '8': [114.0, 112.9, 112.9, 112.9, 112.9],
                         '9': [114.0, 114.0, 112.9, 112.9, 112.9],
                         '10': [112.9, 112.9, 112.9, 112.9, 114.0],
                         '11': [114.0, 112.9, 112.9, 112.9, 112.9],
                         '12': [114.0, 114.0, 112.9, 112.9, 112.9],
                         '13': [112.9, 112.9, 112.9, 112.9, 114.0],
                         '14': [111.4, 118.2, 118.2, 118.2, 118.2],
                         '15': [111.4, 111.4, 118.2, 118.2, 118.2],
                         '16': [118.2, 111.4, 111.4, 118.2, 118.2],
                         '17': [118.2, 118.2, 111.4, 111.4, 118.2],
                         '18': [118.2, 118.2, 118.2, 111.4, 111.4],
                         '19': [118.2, 118.2, 118.2, 118.2, 111.4],
                         '20': [118.2, 118.2, 111.4, 111.4, 118.2],
                         '21': [118.2, 118.2, 118.2, 111.4, 111.4],
                         '22': [118.2, 118.2, 118.2, 118.2, 111.4],
                         '23': [111.4, 118.2, 118.2, 118.2, 118.2],
                         '24': [111.4, 111.4, 118.2, 118.2, 118.2],
                         '25': [118.2, 111.4, 111.4, 118.2, 118.2],
                         '26': [117.7, 117.7, 117.7, 117.7, 117.7],
                         '27': [105.1, 117.7, 117.7, 117.7, 117.7],
                         '28': [117.7, 105.1, 117.7, 117.7, 117.7],
                         '29': [117.7, 117.7, 105.1, 117.7, 117.7],
                         '30': [117.7, 117.7, 117.7, 105.1, 117.7],
                         '31': [117.7, 117.7, 117.7, 117.7, 105.1],
                         '32': [117.7, 117.7, 105.1, 117.7, 117.7],
                         '33': [117.7, 117.7, 117.7, 105.1, 117.7],
                         '34': [117.7, 117.7, 117.7, 117.7, 105.1],
                         '35': [117.7, 117.7, 117.7, 117.7, 117.7],
                         '36': [105.1, 117.7, 117.7, 117.7, 117.7],
                         '37': [117.7, 105.1, 117.7, 117.7, 117.7]}

    values_options = range(0, len(dict_for_ring_dih), 1)

    @staticmethod
    def find(smiles, pyranosering_pattern="C1(CCCCO1)O", positions=None):
        if positions is None:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("The smiles is invalid")
            pattern_pyranosering = Chem.MolFromSmarts(pyranosering_pattern)
            pyranosering = list(mol.GetSubstructMatches(pattern_pyranosering))
            positions = pyranosering
        return positions

    def __init__(self, positions):
        self.name = 'PyranoseRing'
        self.type = "pyranosering"
        self.positions = positions

    def get_random_values(self):
        self.values = [choice(PyranoseRing.values_options)
                       for i in range(len(self.positions))]

    def get_weighted_values(self, weights):
        if len(weights) == len(PyranoseRing.values_options):
            self.values = [PyranoseRing.values_options[find_one_in_list(sum(
                           weights), weights)]
                           for i in range(len(self.positions))]
        else:
            self.values = [choice(PyranoseRing.values_options)
                           for i in range(len(self.positions))]

    def apply_on_string(self, string, values_to_set=None):
        if values_to_set is not None:
            self.values = values_to_set
        for i in range(len(self.positions)):
            val_dih = PyranoseRing.dict_for_ring_dih[str(
                                                     int(self.values[i]))][:5]
            val_ang = PyranoseRing.dict_for_ring_ang[str(
                                                     int(self.values[i]))][:5]
            string = pyranosering_set(string, self.positions[i], val_dih,
                                      val_ang)
        return string

    def update_values(self, string):
        updated_values = []
        for i in range(len(self.positions)):
            updated_values.append(pyranosering_measure(string,
                                  self.positions[i],
                                  PyranoseRing.dict_for_ring_dih))
        self.values = updated_values

    def mutate_values(self, max_mutations=None, weights=None):
        if max_mutations is None:
            max_mutations = max(1, int(math.ceil(len(self.values)/2.0)))
        self.values = mutation(self.values, max_mutations,
                               PyranoseRing.values_options, weights,
                               periodic=False)

    def is_equal(self, other, threshold, chiral=True):
        values = []
        tmp = []
        for i in get_vec(self.values, other.values):
            if i == 0:
                tmp.append(0)
            else:
                tmp.append(1)
        values.append(sum(tmp)/len(tmp))
        if hasattr(other, "initial_values"):
            tmp = []
            for i in get_vec(self.values, other.initial_values):
                if i == 0:
                    tmp.append(0)
                else:
                    tmp.append(1)
            values.append(sum(tmp)/len(tmp))
        if min(values) > threshold:
            return False
        else:
            return True


class CisTrans(DOF):
    values_options = [0.0, 180.0]

    @staticmethod
    def find(smiles, smarts_cistrans=None, positions=None):
        if positions is None:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                raise ValueError("The smiles is invalid")
            pattern_cistrans = Chem.MolFromSmarts(smarts_cistrans)
            cistrans = list(mol.GetSubstructMatches(pattern_cistrans))
            positions = cleaner(cistrans)
        return positions      

    def __init__(self, positions):
        self.name = 'CisTrans'
        self.type = "cistrans"
        self.positions = positions

    def apply_on_string(self, string, values_to_set=None):

        if values_to_set is not None:
            self.values = values_to_set

        for i in range(len(self.positions)):
            string = dihedral_set(string, self.positions[i], self.values[i])
        return string

    def update_values(self, string):
        updated_values = []
        for i in range(len(self.positions)):
            updated_values.append(dihedral_measure(string, self.positions[i]))
        self.values = updated_values

    def get_random_values(self):
        self.values = [choice(CisTrans.values_options)
                       for i in range(len(self.positions))]

    def get_weighted_values(self, weights):
        if len(weights) == len(CisTrans.values_options):
            self.values = [CisTrans.values_options[find_one_in_list(sum(
                           weights), weights)]
                           for i in range(len(self.positions))]
        else:
            self.values = [choice(CisTrans.values_options)
                           for i in range(len(self.positions))]

    def mutate_values(self, max_mutations=None, weights=None):

        if max_mutations is None:
            max_mutations = max(1, int(math.ceil(len(self.values)/2.0)))

        self.values = mutation(self.values, max_mutations,
                               CisTrans.values_options, weights, periodic=True)

    def is_equal(self, other, threshold, chiral=True):
        values = []
        values.append(tor_rmsd(2, get_vec(self.values, other.values)))

        if hasattr(other, "initial_values"):
            values.append(tor_rmsd(2, get_vec(self.values,
                                              other.initial_values)))

        if not chiral:
            values.append(tor_rmsd(2, get_vec(self.values,
                                              [-1*i for i in other.values])))
            if hasattr(other, "initial_values"):
                values.append(tor_rmsd(2, get_vec(self.values,
                                       [-1*i for i in other.initial_values])))
        if min(values) > threshold:
            return False
        else:
            return True
#=======================================================================
#~ '''
#~ For test of the module only
#~ '''

#~ smiles = 'CC(=O)N[C@H](C(=O)NC)C'
#~ obj = Centroid(smiles)
#~ mol = Chem.MolFromSmiles(obj.positions)
#~ mol = Chem.AddHs(mol)
#~ AllChem.EmbedMolecule(mol)
#~ string = Chem.MolToMolBlock(mol)




#~ coords_and_masses = get_coords_and_masses(string)
#~ positions = coords_and_masses[:,:3]
#~ weights = coords_and_masses[:,3]

#~ quaternion = np.array([90,0,0,1])
#~ quaternion_set(string, quaternion)

#~ print 'Marianas tensor of inertia:\n{}'.format(cm_and_inertia(positions, weights))
#~ print 'My tensor of inertia:\n{}'.format(get_tensor_of_inertia(string))
#~ print 'Initial coordinates:'
#~ print sdf2xyz(string)
#~ print 'Initial centroid:'
#~ print centroid_measure(string)
#~ obj.get_random_values()
#~ print 'Centroid will be set to:'
#~ print obj.values
#~ string = obj.apply_on_string(string, obj.values)
#~ print 'Final coordinates:'
#~ print sdf2xyz(string)
#~ print 'Final centroid:'
#~ print centroid_measure(string)
#***********************************************************************






