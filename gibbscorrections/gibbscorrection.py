#!/usr/bin/env python3

"""Gibbs Correction

A module that automatises the tedious process of retrieving a Gaussian 16 geometry, and setting up and running a single
point Orca calculation at that geometry. Of course, for a bunch of files at the same time.
"""

import sys
import argparse


def main(arguments):

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("infile", help="Input file", type=argparse.FileType("r"))
    parser.add_argument(
        "-o",
        "--outfile",
        help="Output file",
        default=sys.stdout,
        type=argparse.FileType("w"),
    )

    args = parser.parse_args(arguments)

    print(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
