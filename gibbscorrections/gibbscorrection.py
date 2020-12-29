#!/usr/bin/env python3

"""Gibbs Correction

A module that automatises the tedious process of retrieving a Gaussian 16 geometry, and setting up and running a single
point Orca calculation at that geometry. Of course, for a bunch of files at the same time.
"""
import logging
import os
import sys
import argparse

import cclib as cclib


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
    molecules = [get_coordinates(mol) for mol in args["input_files"]]


def get_coordinates(gaussian_file):
    """Retrieve coordinates from Gaussian calculation log file"""
    file = cclib.io.ccread(gaussian_file)
    data = file.parse()
    return data.coordinates[-1]


def help_description():
    pass


def help_epilog():
    pass


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
        "-i", "--input_files", type=str, nargs="+", help="List of files for which a single point is necessary"
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
        default="wB97MV",
        help="Functional used for the computation, as wB97MV or M062X",
    )
    parser.add_argument(
        "-b",
        "--basisset",
        type=str,
        nargs="?",
        default="Def2TZVP",
        help="The basis set to use for all atoms",
    )
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as error:
        print(str(error))  # Print something like "option -a not recognized"
        sys.exit(2)

    # Setup file names
    values["input_files"] = [os.path.abspath(i) for i in args.input_file]
    logger.debug("Input files: %s", values["input_file"])
    values["output_file"] = os.path.abspath(args.output_file[0])
    logger.debug("Output file: %s", values["output_file"])

    # Parse functional
    functional = args.functional.split("-")
    values["functional"] = functional[0]
    logger.debug("Functional: %s", values["functional"])

    # Parse basis set
    values["basisset"] = args.basisset
    logger.debug("Basis set: %s", values["basisset"])

    # All values are retrieved, return the table
    return values


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


if __name__ == "__main__":
    sys.exit(main())
