from pathlib import Path
from typing import NamedTuple

import numpy as np
from numpy import typing as npt

from dat2npy.types import Seconds


class DatFile(NamedTuple):
    """Contain all information about .dat file

    Attributes
    ----------
    signal : npt.NDArray[np.float32]
        Electrogram signal array (2-dimensional: 0 - channel, 1 - signal itself)
    start_time : Seconds
        The start time of the recording
    stop_time : Seconds
        The stop time of the recording
    filepath : Path
        Path to .dat file
    channel_names : tuple[str]
        Names of electrodes (typically consists of something like "A1" or "B2", etc.)
    """

    signal: npt.NDArray[np.float32]
    start_time: Seconds
    stop_time: Seconds
    filepath: Path
    channel_names: tuple[str]


def parse_float(string: str) -> float:
    return float(string.replace(",", "."))


def read_file(filepath: Path) -> DatFile:
    with open(filepath, "r") as input_:
        header = input_.readline()
        # ["A1(x)" "A1(y)" "A2(x)" "A2(y)"] <-- Example input
        # Strip last 3 characters to remove redundant (x) or (y)
        # Get every 2nd to remove duplicates
        # ["A1", "A2"] <-- Example output for example input above
        channel_names = tuple(channel_name[:-3] for channel_name in header.split()[::2])

        # Read lines of floats to convert them to numpy array and transpose
        lines: list[list[float]] = []

        # Corner case for first line in purpose to get start time of the recording
        line = input_.readline().split()
        start_time: Seconds = parse_float(line[0])
        stop_time: Seconds = start_time
        lines.append([parse_float(elem) for elem in line[1::2]])

        while (line := input_.readline().split()):
            lines.append([parse_float(elem) for elem in line[1::2]])
            stop_time = max(parse_float(line[0]), stop_time)

    signal = np.array(lines, dtype=np.float32).transpose()

    dat_file = DatFile(
        signal=signal,
        start_time=start_time,
        stop_time=stop_time,
        filepath=filepath,
        channel_names=channel_names,
    )

    return dat_file
