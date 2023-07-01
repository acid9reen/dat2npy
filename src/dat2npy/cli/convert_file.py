import argparse
from pathlib import Path

import numpy as np

from dat2npy.dat_utils import read_dat_file


class FileConverterNamespace(argparse.Namespace):
    filepath: Path


def parse_args() -> FileConverterNamespace:
    parser = argparse.ArgumentParser(
        description="Convert specified .dat file to .npy",
        epilog=(
            "P.S. Created file will be saved in the directory"
            "of the given one to convert"
        ),
    )

    parser.add_argument(
        "filepath",
        type=Path,
        help="Path to .dat file to convert to .npy",
    )

    return parser.parse_args(namespace=FileConverterNamespace())


def main() -> int:
    args = parse_args()
    dat_file = read_dat_file(args.filepath)

    # Create output file path
    output_filename = args.filepath.stem + ".npy"
    output_filepath = args.filepath.parent / output_filename

    np.save(output_filepath, dat_file.signal)

    return 0
