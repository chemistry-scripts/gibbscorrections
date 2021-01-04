#!/usr/bin/env python3

"""Gibbs Correction

A module that automatises the tedious process of retrieving a Gaussian 16 geometry, and setting up and running a single
point Orca calculation at that geometry. Of course, for a bunch of files at the same time.
"""
import logging
import sys
import argparse
from pathlib import Path

import cclib as cclib
from cclib.parser.utils import PeriodicTable, convertor
from molecule import Molecule
from orca_job import OrcaJob


def main():
    """
    Main function

    Basic structure is:
    - Setup helpers (arguments, logging, etc.)
    - Parse all input files to retrieve all useful data (final geometries)
    - Setup Orca calculations
    - Run Orca calculations
    - Parse output and save data
    - Write output file with all relevant data, recomputed and converted
    """

    # Set up the script (logging, parse arguments, etc.)
    setup_logging()
    args = get_input_arguments()

    # Parse input files
    list_coordinates = [get_coordinates(mol) for mol in args["input_files"]]
    list_atom_lists = [get_atom_lists(mol) for mol in args["input_files"]]
    list_filenames = [get_file_name(file) for file in args["input_files"]]

    # Setup orca computations
    molecules = [
        # TODO: Add name to orca_job
        Molecule(coordinates, list_of_atoms)
        for coordinates, list_of_atoms in zip(list_coordinates, list_atom_lists)
    ]
    # TODO: properly include all data in OrcaJob constructor
    basedir = Path().cwd()
    orca_arguments = get_orca_arguments(args["functional"], args["basisset"])
    computations = [
        OrcaJob(
            molecule=mol,
            name=name,
            basedir=basedir,
            job_id=name,
            orca_args=orca_arguments,
        )
        for mol, name in zip(molecules, list_filenames)
    ]

    # Write orca files
    [job.setup_computation() for job in computations]

    # Run Orca
    # TODO: parallelize
    [job.run() for job in computations]


def get_orca_arguments(functional, basisset):
    """Returns the required first line for a typical orca calculation using the functional and basisset provided"""
    orca_args = {"functional": functional, "basisset": basisset}
    return orca_args


def get_coordinates(gaussian_file):
    """Retrieve coordinates from Gaussian calculation log file"""
    file = cclib.io.ccread(gaussian_file.resolve().as_posix())
    return file.atomcoords[-1]


def get_atom_lists(gaussian_file):
    """Returns the list of atoms in the input order"""
    file = cclib.io.ccread(gaussian_file.resolve().as_posix())
    atoms = file.atomnos.tolist()
    periodic_table = PeriodicTable()
    atom_list = [periodic_table.element[i] for i in atoms]
    return atom_list


def get_file_name(gaussian_file):
    """Return file name (removes .log)"""
    return Path(gaussian_file).stem


def setup_logging():
    """Setup logging for module"""
    # Setup logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: %(message)s")
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)


def get_input_arguments():
    """Check command line options and accordingly set computation parameters."""
    logger = logging.getLogger()

    # List of values to extract
    values = dict.fromkeys(
        [
            "input_files",
            "output_file",
            "functional",
            "basisset",
        ]
    )

    # Basic parser setup
    parser = argparse.ArgumentParser(
        description=help_description(), epilog=help_epilog()
    )
    parser.formatter_class = argparse.RawDescriptionHelpFormatter

    # Add arguments to parser
    parser.add_argument(
        "-i",
        "--input_files",
        type=str,
        nargs="+",
        help="List of files for which a single point is necessary",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        nargs=1,
        help="Output file in which to print the energy values",
    )
    parser.add_argument(
        "-f",
        "--functional",
        type=str,
        nargs="?",
        default="wB97M-V",
        help="Functional used for the computation, as wB97M-V or M062X",
    )
    parser.add_argument(
        "-b",
        "--basisset",
        type=str,
        nargs="?",
        default="Def2-TZVPP",
        help="The basis set to use for all atoms",
    )
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as error:
        print(str(error))  # Print something like "option -a not recognized"
        sys.exit(2)

    # Setup file names
    # Todo: check validity of pathlib use (absolute?)
    values["input_files"] = [Path(i) for i in args.input_files]
    logger.debug("Input files: %s", values["input_files"])
    values["output_file"] = Path(args.output_file[0])
    logger.debug("Output file: %s", values["output_file"])

    # Parse functional
    values["functional"] = args.functional
    logger.debug("Functional: %s", values["functional"])

    # Parse basis set
    values["basisset"] = args.basisset
    logger.debug("Basis set: %s", values["basisset"])

    # All values are retrieved, return the table
    return values


def help_description():
    pass


def help_epilog():
    pass


if __name__ == "__main__":
    sys.exit(main())
