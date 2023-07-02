import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.signal import decimate

from dat2npy.constants import CHANNEL_NAME_TO_INDEX
from dat2npy.dat import DatFileMeta
from dat2npy.dat import read_dat_file
from dat2npy.types import Hz


class CreateDatasetNamespace(argparse.Namespace):
    dat_files_folder: Path
    labels_files_folder: Path
    target_frequency: Hz | None = None
    output_folder: Path


def parse_args() -> CreateDatasetNamespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert specified .dat file to .npy "
            "and create files with labels"
        ),
    )

    parser.add_argument(
        "dat_files_folder",
        type=Path,
        help="Path to .dat files to convert to .npy",
    )

    parser.add_argument(
        "labels_files_folder",
        type=Path,
        help="Path to .json files with labels",
    )

    parser.add_argument(
        "-f",
        "--target_frequency",
        type=Hz,
        default=None,
        help=(
            "Target frequency for output signal, "
            "must be less than frequency in original signal"
        ),
    )

    parser.add_argument(
        "output_folder",
        type=Path,
        help="Path to folder for X and Y subfolders",
    )

    return parser.parse_args(namespace=CreateDatasetNamespace())


def process_experiment(
    signal_paths: list[Path],
    label_path: Path,
    target_frequency: Hz | None,
    signals_output_folder: Path,
    labels_output_folder: Path,
    experiment: str,
) -> None:
    file_metas: list[DatFileMeta] = []
    labels = json.loads(label_path.read_text())

    for path in signal_paths:
        dat_file = read_dat_file(path)
        file_metas.append(dat_file.meta)

        signal_to_save = (
            dat_file.signal if target_frequency is None
            else decimate(
                dat_file.signal,
                q=round(dat_file.meta.frequency/target_frequency),
                axis=1,
            )
        )

        filename = (
            f"{experiment}_{'-'.join(dat_file.meta.channel_names)}_"
            f"{dat_file.meta.start_time}-{dat_file.meta.stop_time}_"
            f"{target_frequency or dat_file.meta.frequency}"
        )

        npy_filename = "X_" + filename + ".npy"
        np.save(signals_output_folder / npy_filename, signal_to_save)

        label = [[] for __ in range(len(dat_file.meta.channel_names))]

        channels = [
            CHANNEL_NAME_TO_INDEX[channel_name]
            for channel_name in dat_file.meta.channel_names
        ]

        for channel_index, channel in enumerate(channels):
            for elem in labels[channel]:
                converted_elem = elem / 5000
                more_than = dat_file.meta.start_time <= converted_elem
                less_than = converted_elem <= dat_file.meta.stop_time

                if more_than:
                    if less_than:
                        label[channel_index].append(
                            elem * round(
                                (target_frequency or dat_file.meta.frequency) / 5_000,
                            ) - round(dat_file.meta.start_time * 5_000),
                        )
                    else:
                        break

        label_filename = "Y_" + filename + ".json"
        with open(labels_output_folder / label_filename, "w") as out:
            json.dump(label, out)


def main() -> int:
    args = parse_args()
    dat_file_paths = args.dat_files_folder.rglob("*.dat")
    label_file_paths = args.labels_files_folder.rglob("*.json")

    experiment_dat_files: defaultdict[str, list[Path]] = defaultdict(list)

    for dat_file_path in dat_file_paths:
        # Example: "H25 ph0 A1-A3 A8 0-120 sec 20kHz" -> "25_ph0"
        experiment = "_".join(dat_file_path.stem.split()[:2])[1:].casefold()
        experiment_dat_files[experiment].append(dat_file_path)

    experiment_label_path: dict[str, Path] = {}

    for label_file_path in label_file_paths:
        experiment = label_file_path.stem[2:].casefold()
        experiment_label_path[experiment] = label_file_path

    files_output_folder = args.output_folder / "X"
    files_output_folder.mkdir(exist_ok=True)

    labels_output_folder = args.output_folder / "Y"
    labels_output_folder.mkdir(exist_ok=True)

    for experiment, dat_file_paths in experiment_dat_files.items():
        label_file_path = experiment_label_path[experiment]
        process_experiment(
            dat_file_paths,
            label_file_path,
            args.target_frequency,
            files_output_folder,
            labels_output_folder,
            experiment,
        )

    return 0
