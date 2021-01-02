#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, E. Nicolas

"""Class representing a molecule"""

from cclib.parser.utils import PeriodicTable


class Molecule:
    """
    Class that represents a molecule

    Attributes:
        - coordinates (list of XYZ coordinates)
        - natoms (number of atoms, int)
        - elements_list (list of elements as in periodic table class from cclib)

    """

    def __init__(self, coordinates, elements_list):
        """Build  the Molecule class."""
        if not len(coordinates) == len(elements_list):
            raise ValueError("Coordinates and Elements are not the same size")
        self._coordinates = coordinates
        self._elements_list = elements_list
        self._natoms = len(elements_list)

    @property
    def coordinates(self):
        """Returns coordinates"""
        return self._coordinates

    @coordinates.setter
    def coordinates(self, value):
        if not len(value) == self.natoms:
            raise ValueError("Coordinates and Elements are not the same size")
        self._coordinates = value

    @property
    def elements_list(self):
        """Returns list of elements"""
        return self._elements_list

    @elements_list.setter
    def elements_list(self, value):
        if not len(value) == self.natoms:
            raise ValueError("Coordinates and Elements are not the same size")
        self._elements_list = value

    @property
    def natoms(self):
        """Returns number of atoms"""
        return self._natoms

    @natoms.setter
    def natoms(self, value):
        self._natoms = value

    def xyz_geometry(self):
        """Returns geometry in XYZ format"""
        periodic_table = PeriodicTable()

        xyz_geometry = [
            " ".join(
                [periodic_table.element[self.elements_list[i]].ljust(5)]
                + ["{:.6f}".format(s).rjust(25) for s in atom]
            )
            for i, atom in enumerate(self.coordinates)
        ]

        return xyz_geometry
