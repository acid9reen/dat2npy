import argparse
from pathlib import Path


class FileConverterNamespace(argparse.Namespace):
    filepath: Path


def parse_args() -> FileConverterNamespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "filepath",
        type=Path,
        help="Path to .dat file to convert to .npy",
    )

    return parser.parse_args(namespace=FileConverterNamespace())


def main() -> int:
    parse_args()

    return 0
