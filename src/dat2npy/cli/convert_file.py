import argparse
from pathlib import Path

import numpy as np
from scipy.signal import decimate

from dat2npy.dat_utils import read_dat_file
from dat2npy.types import Hz


class FileConverterNamespace(argparse.Namespace):
    filepath: Path
    target_frequency: Hz | None = None


def parse_args() -> FileConverterNamespace:
    parser = argparse.ArgumentParser(
        description="Convert specified .dat file to .npy",
        epilog=(
            "P.S. Created file will be saved in the directory "
            "of the given one to convert"
        ),
    )

    parser.add_argument(
        "filepath",
        type=Path,
        help="Path to .dat file to convert to .npy",
    )

    parser.add_argument(
        "-f",
        "--target_frequency",
        type=Hz,
        help=(
            "Target frequency for output signal, "
            "must be less than frequency in original signal"
        ),
    )

    return parser.parse_args(namespace=FileConverterNamespace())


def main() -> int:
    args = parse_args()
    dat_file = read_dat_file(args.filepath)

    # Create output file path
    output_filename = args.filepath.stem + ".npy"
    output_filepath = args.filepath.parent / output_filename

    signal_to_save = (
        dat_file.signal if args.target_frequency is None
        else decimate(
            dat_file.signal,
            q=round(dat_file.frequency/args.target_frequency),
            axis=1,
        )
    )

    np.save(output_filepath, signal_to_save)

    return 0
