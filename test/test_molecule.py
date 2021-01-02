#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, E. Nicolas

"""Tests for molecule class"""

from gibbscorrections.molecule import Molecule
import pytest


@pytest.fixture
def molecule_hydrogen():
    elements_list = [1, 1]
    coordinates = [[0.0000, 0.0000, 0.0000], [0.0000, 0.0000, 0.7400]]
    return Molecule(coordinates, elements_list)


@pytest.fixture
def molecule_platinum_hydride():
    elements_list = [78, 1, 1, 1, 1]
    coordinates = [
        [-0.0126981359, 1.0858041578, 0.0080009958],
        [0.002150416, -0.0060313176, 0.0019761204],
        [1.0117308433, 1.4637511618, 0.0002765748],
        [-0.540815069, 1.4475266138, -0.8766437152],
        [-0.5238136345, 1.4379326443, 0.9063972942],
    ]
    return Molecule(coordinates, elements_list)


def test_xyz_geometry(molecule_hydrogen, molecule_platinum_hydride):
    """Testing xyz geometry generator"""
    geometry_hydrogen = [
        "H                      0.000000                  0.000000                  0.000000",
        "H                      0.000000                  0.000000                  0.740000",
    ]

    geometry_platinum_hydride = [
        "Pt                    -0.012698                  1.085804                  0.008001",
        "H                      0.002150                 -0.006031                  0.001976",
        "H                      1.011731                  1.463751                  0.000277",
        "H                     -0.540815                  1.447527                 -0.876644",
        "H                     -0.523814                  1.437933                  0.906397",
    ]

    xyz_geometry_hydrogen = molecule_hydrogen.xyz_geometry()
    assert xyz_geometry_hydrogen == geometry_hydrogen
    xyz_geometry_platinum_hydride = molecule_platinum_hydride.xyz_geometry()
    assert xyz_geometry_platinum_hydride == geometry_platinum_hydride
