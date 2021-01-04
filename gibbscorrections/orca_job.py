#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019, E. Nicolas

"""Orca Job class to start job, run it and analyze it"""
import logging
import os
import shutil
from cclib.io import ccread
from cclib.parser.utils import PeriodicTable


class OrcaJob:
    """
    Class that can be used as a container for Orca jobs.

    Attributes:
        - basedir (base directory, os.path object)
        - name (name of computation, string)
        - coordinates (list of XYZ coordinates)
        - job_id (unique identifier, int)
        - natoms (number of atoms, int)
        - path (path in which to run current computation, os.path object)
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
        path = os.path.join(
            self.basedir, self.name.replace(" ", "_") + "." + str(self.job_id).zfill(8)
        )
        return path

    @property
    def molecule(self):
        """Molecule specification (coords, natoms, etc)"""
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
    def footer(self):
        """Computation footer"""
        return self.build_footer()

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
        # Get into workdir, start Orca, then back to basedir
        os.chdir(self.path)
        os.system("g16 < " + self.filenames["input"] + " > " + self.filenames["output"])
        os.chdir(self.basedir)
        # Log end of computation
        logging.info("Orca finished: %s", str(self.name))
        return

    def extract_natural_charges(self):
        """Extract NBO Charges parsing the output file."""
        # Log start
        logging.info("Parsing results from computation %s", str(self.job_id))

        # Get into working directory
        os.chdir(self.path)

        # Initialize charges list
        charges = []

        with open(self.filenames["output"], mode="r") as out_file:
            line = "Foobar line"
            while line:
                line = out_file.readline()
                if "Summary of Natural Population Analysis:" in line:
                    logging.debug("ID %s: Found NPA table.", str(self.job_id))
                    # We have the table we want for the charges
                    # Read five lines to remove the header:
                    # Summary of Natural Population Analysis:
                    #
                    # Natural Population
                    # Natural    ---------------------------------------------
                    # Atom No    Charge        Core      Valence    Rydberg      Total
                    # ----------------------------------------------------------------
                    for _ in range(0, 5):
                        out_file.readline()
                    # Then we read the actual table:
                    for _ in range(0, self.molecule.natoms):
                        # Each line follow the header with the form:
                        # C  1    0.92349      1.99948     3.03282    0.04422     5.07651
                        line = out_file.readline()
                        line = line.split()
                        charges.append(line[2])
                    logging.debug(
                        "ID %s: Charges = %s",
                        str(self.job_id),
                        " ".join([str(i) for i in charges]),
                    )
                    # We have reached the end of the table, we can break the while loop
                    break
                # End of if 'Summary of Natural Population Analysis:'
        # Get back to the base directory
        os.chdir(self.basedir)
        return charges

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
        energies["enthalpy"] = data.enthalpy
        energies["freeenergy"] = data.freeenergy

        return energies

    def build_header(self):
        """
        Builds the top part used for the Orca calculation.

        List of strings expected
        """
        header = list()
        header.append("%NProcShared=1")
        # header.append('%Mem=' + args['memory'])
        route = "# " + self.orca_args["functional"] + " "
        if self.orca_args["dispersion"] is not None:
            route += "EmpiricalDispersion=" + self.orca_args["dispersion"] + " "
        route += "gen freq"
        header.append(route)
        header.append("")
        # To update probably
        header.append(self.name)
        header.append("")
        # This is a singlet. Careful for other systems!
        header.append("0 1")

        logging.debug("Header: \n %s", "\n".join(header))
        return header

    def build_footer(self):
        """
        Builds the bottom part used for the Orca calculation.

        List of strings.
        """
        footer = []

        # Basis set is the same for all elements. No ECP either.
        # Remove duplicates, and convert to element name
        periodic_table = PeriodicTable()
        elements = [
            periodic_table.element[el] for el in list(set(self.molecule.elements_list))
        ]

        elements = " ".join(elements)
        basisset = self.orca_args["basisset"]
        footer.append(elements + " 0")
        footer.append(basisset)
        footer.append("****")
        footer.append("")

        # footer.append("$NBO")
        # # NBO_FILES should be updated to something more useful
        # footer.append("FILE=NBO_FILES")
        # footer.append("PLOT")
        # footer.append("$END")

        logging.debug("Footer: \n %s", "\n".join(footer))
        return footer

    def build_input_script(self):
        """Build full input script"""
        script = []
        # Put header
        script.extend(self.header)

        # Add geometry + blank line
        script.extend(self.molecule.xyz_geometry())
        script.append("")

        # Add footer
        script.extend(self.footer)

        # Add two blank lines for the sake of Orca's weird behavior
        script.append("")
        script.append("")

        return script

    def cleanup(self):
        """Removing folders and files once everything is run and extracted"""
        logging.info("Removing directory: %s", str(self.path))
        shutil.rmtree(self.path)
        return
