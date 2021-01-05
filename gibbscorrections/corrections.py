#!/usr/bin/env python3

"""
Gibbs Correction

A module that automatises the tedious process of retrieving a Gaussian 16 geometry, and setting up and running a single
point Orca calculation at that geometry. Of course, for a bunch of files at the same time.
"""
import logging
import multiprocessing
import sys
import argparse
from pathlib import Path

import cclib as cclib
from cclib.parser.utils import convertor
from gibbscorrections.molecule import Molecule
from gibbscorrections.orca_job import OrcaJob


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
    list_energies = [get_energies(mol) for mol in args["input_files"]]

    # Setup orca computations
    molecules = [
        Molecule(coordinates, list_of_atoms)
        for coordinates, list_of_atoms in zip(list_coordinates, list_atom_lists)
    ]
    basedir = Path().cwd()
    orca_arguments = {key: value for key,value in args.items() if key in ["functional", "basisset", "solvent"]}
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

    # Run Orca jobs in parallel
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    orca_results = pool.map(run_jobs, computations)

    # Retrieve SCF energies
    scf_energies = [result.get_energies()["scfenergy"] for result in orca_results]

    # Print everything neatly to output file
    print_results(args["output_file"], scf_energies, list_energies, list_filenames)


def run_jobs(job):
    job.run()
    return job


def print_results(out_file, scf_energies, list_energies, list_filenames):
    """Print results from Orca calculations together with gaussian original results and corrected values"""
    with open(out_file, mode="w") as outfile:
        header = "Name\tGaussian SCF\tGaussian H\tGaussian G\tOrca SCF\tOrca H\tOrca G"
        outfile.write(header + "\n")
        for name, orca_energy, gaussian_energies in zip(list_filenames, scf_energies, list_energies):
            # Create all intermediate data to print
            orca_freeenergy = orca_energy + gaussian_energies["freeenergy_correction"]
            orca_enthalpy = orca_energy + gaussian_energies["enthalpy_correction"]

            energies = [
                gaussian_energies["scfenergy"],
                gaussian_energies["enthalpy"],
                gaussian_energies["freeenergy"],
                orca_energy,
                orca_enthalpy,
                orca_freeenergy,
            ]

            # Convert to kcal/mol from Hartree
            energies_kcal = [str(convertor(val, "eV", "kcal/mol")) for val in energies]

            # Create line
            line = name + "\t" + "\t".join(energies_kcal)
            outfile.write(line + "\n")


def get_energies(comp_file):
    """Retrieve energies from calculation log file"""
    file = cclib.io.ccread(comp_file.resolve().as_posix())
    energies = dict.fromkeys(
        [
            "scfenergy",
            "enthalpy",
            "freeenergy",
            "enthalpy_correction",
            "freeenergy_correction",
        ]
    )
    energies["scfenergy"] = file.scfenergies[-1]
    if file.enthalpy:
        energies["enthalpy"] = file.enthalpy
        energies["enthalpy_correction"] = energies["enthalpy"] - energies["scfenergy"]
    if file.freeenergy:
        energies["freeenergy"] = file.freeenergy
        energies["freeenergy_correction"] = (
            energies["freeenergy"] - energies["scfenergy"]
        )

    return energies


def get_coordinates(comp_file):
    """Retrieve coordinates from Gaussian calculation log file"""
    file = cclib.io.ccread(comp_file.resolve().as_posix())
    return file.atomcoords[-1]


def get_atom_lists(comp_file):
    """Returns the list of atoms in the input order"""
    file = cclib.io.ccread(comp_file.resolve().as_posix())
    atom_list = file.atomnos.tolist()
    return atom_list


def get_file_name(file):
    """Return file name (removes .log)"""
    return Path(file).stem


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
            "solvent"
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
        help="Functional used for the computation, such as wB97M-V or M062X. See the Orca Manual for syntax.",
    )
    parser.add_argument(
        "-b",
        "--basisset",
        type=str,
        nargs="?",
        default="Def2-TZVPP",
        help="The basis set to use for all atoms. Not to change lightly, other basis sets not properly implemented.",
    )
    parser.add_argument(
        "-s",
        "--solvent",
        type=str,
        nargs="?",
        help="Solvent to use with SMD Model, as described in the Orca user manual.",
    )
    try:
        args = parser.parse_args()
    except argparse.ArgumentError as error:
        print(str(error))  # Print something like "option -a not recognized"
        sys.exit(2)

    # Setup file names
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

    # Parse solvent
    values["solvent"] = args.solvent
    logger.debug("Solvent: %s", values["solvent"])

    # All values are retrieved, return the table
    return values


def help_description():
    pass


def help_epilog():
    pass


if __name__ == "__main__":
    sys.exit(main())
