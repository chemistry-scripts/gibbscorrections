#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, E. Nicolas

"""Orca Job class to start job, run it and analyze it"""
import logging
import os
from pathlib import Path
import shutil
from cclib.io import ccread


class OrcaJob:
    """
    Class that can be used as a container for Orca jobs.

    Attributes:
        - basedir (base directory, os path object)
        - name (name of computation, string)
        - coordinates (list of XYZ coordinates)
        - job_id (unique identifier, int)
        - n_atoms (number of atoms, int)
        - path (path in which to run current computation, os path object)
        - filenames (dict with input, (file_name.com, str)
                               output, (file_name.log, str)
                    )
        - input_script (input file, list of strings)

    """

    def __init__(self, basedir, name, molecule, job_id, orca_args):
        """Build  the OrcaJob class."""
        # Populate the class attributes
        self._name = name
        self._molecule = molecule
        self._job_id = job_id
        self._basedir = basedir
        self.filenames = dict()
        self.filenames["input"] = self.name.replace(" ", "_") + ".inp"
        self.filenames["output"] = self.name.replace(" ", "_") + ".out"
        self._orca_args = orca_args

    @property
    def path(self):
        """
        Computation path, calculated at will as: /basedir/my_name.00job_id/
        """
        path = Path().joinpath(self.basedir, self.name)
        return path

    @property
    def molecule(self):
        """Molecule specification (coordinates, n_atoms, etc)"""
        return self._molecule

    @molecule.setter
    def molecule(self, value):
        self._molecule = value

    @property
    def name(self):
        """Job Name"""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def job_id(self):
        """Job id"""
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        self._job_id = value

    @property
    def basedir(self):
        """Directory of Orca job"""
        return self._basedir

    @basedir.setter
    def basedir(self, value):
        self._basedir = value

    @property
    def header(self):
        """Computation header"""
        return self.build_header()

    @property
    def geometry(self):
        """Computation footer"""
        return self.get_geometry_block()

    @property
    def orca_args(self):
        """
        All arguments necessary for the Orca computation:
            - Functional
            - Dispersion or not ?
            - Basis set (One for all atoms. Choose wisely !)
        """
        return self._orca_args

    @orca_args.setter
    def orca_args(self, value):
        self._orca_args = value

    def run(self):
        """Start the job."""
        # Log computation start
        logging.info("Starting Orca: %s", str(self.name))
        # Get into workdir, if computation not already done start Orca, then back to basedir
        os.chdir(self.path)
        if self.computation_finished():
            logging.info("Orca was not started: %s was already computed", str(self.name))
        else:
            os.system(
                "$ORCA_BIN_DIR/orca "
                + self.filenames["input"]
                + " > "
                + self.filenames["output"]
            )
            logging.info("Orca finished: %s", str(self.name))
        os.chdir(self.basedir)
        # Log end of computation
        logging.info("Orca finished: %s", str(self.name))
        return

    def computation_finished(self):
        """Check if computation in current directory is finished."""
        if os.path.isfile(self.filenames["output"]):
            with open(self.filenames["output"], "r") as out_file:
                for line in out_file.readlines():
                    if "****ORCA TERMINATED NORMALLY****" in line:
                        return True
        return False

    def extract_natural_charges(self):
        """Extract NBO Charges parsing the output file."""
        # Log start
        logging.info("Parsing results from computation %s", str(self.job_id))
        pass

    def get_coordinates(self):
        """Extract coordinates from output file."""
        # Log start
        logging.info("Extracting coordinates for job %s", str(self.job_id))

        # Get into working directory
        os.chdir(self.path)

        # Parse file with cclib
        data = ccread(self.filenames["output"], loglevel=logging.WARNING)

        #  Return the first coordinates, since it is a single point
        return data.atomcoords[0]

    def setup_computation(self):
        """
        Set computation up before running it.

        Create working directory, write input file
        """
        # Create working directory
        os.makedirs(self.path, mode=0o777, exist_ok=True)
        logging.info("Created directory %s", self.path)
        # Go into working directory
        os.chdir(self.path)
        # Write input file
        with open(self.filenames["input"], mode="w") as input_file:
            input_file.write("\n".join(self.build_input_script()))
        logging.debug("Wrote file %s", self.filenames["input"])
        # Get back to base directory
        os.chdir(self.basedir)

    def get_energies(self):
        """
        Retrieve HF energies plus thermochemical corrections

        :return:
        """
        # Log start
        logging.info("Extracting energies from %s", self.name)

        # Get into working directory
        os.chdir(self.path)

        # Parse file with cclib
        data = ccread(self.filenames["output"], loglevel=logging.WARNING)

        #  Return the parsed energies as a dictionary
        energies = dict.fromkeys(["scfenergy", "enthalpy", "freeenergy"])
        energies["scfenergy"] = data.scfenergies[-1]
        energies["enthalpy"] = data.enthalpy if hasattr(data, "enthalpy") else None
        energies["freeenergy"] = (
            data.freeenergy if hasattr(data, "freeenergy") else None
        )

        return energies

    def build_header(self):
        """
        Builds the top part used for the Orca calculation.

        List of strings expected
        """
        header = list()
        line = (
            "! RKS "
            + self.orca_args["functional"]
            + " "
            + self.orca_args["basisset"]
            + " "
            + self.orca_args["basisset"]
            + "/c def2/j tightscf rijcosx"
        )
        header.append(line)
        header.append("")
        header.append("%pal nprocs 4 end")
        header.append("")
        logging.debug("Header: \n %s", "\n".join(header))
        return header

    def get_geometry_block(self):
        """
        Builds the geometry block for Orca.

        List of strings.
        """
        block = [
            "* xyz " + str(self.molecule.charge) + " " + str(self.molecule.multiplicity)
        ]
        block.extend(self.molecule.xyz_geometry())
        block.append("*")
        logging.debug("Geometry block: \n %s", "\n".join(block))
        return block

    def get_solvation_block(self):
        """Build solvation block command, with SMD model"""
        block = [
            "! CPCM",
            "%cpcm",
            "smd True",
            'SMDSolvent "' + self.orca_args["solvent"] + '"',
            "end",
        ]
        return block

    def build_input_script(self):
        """Build full input script"""
        script = []
        # Put header
        script.extend(self.header)

        # Include solvent if it has been set
        if self.orca_args["solvent"]:
            script.extend(self.get_solvation_block())
            script.append("")

        # Add geometry
        script.extend(self.geometry)

        # Add one blank line to finish file
        script.append("")

        return script

    def cleanup(self):
        """Removing folders and files once everything is run and extracted"""
        logging.info("Removing directory: %s", str(self.path))
        shutil.rmtree(self.path)
        return
