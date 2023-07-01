import gc
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Callable
from typing import Generator
from typing import NamedTuple
from typing import ParamSpec
from typing import TypeVar

import numpy as np
from numpy import typing as npt

from dat2npy.types import Hz
from dat2npy.types import Seconds


@contextmanager
def no_gc() -> Generator[None, None, None]:
    """Context manager to run code without garbage collector

    Yields
    ------
    Generator[None, None, None]
        Nothing
    """

    if gc.isenabled():
        gc.disable()
        yield
        gc.enable()
    else:
        yield


_P = ParamSpec("_P")
_RT = TypeVar("_RT")


def disable_gc(func: Callable[_P, _RT]) -> Callable[_P, _RT]:
    """Run function without garbage collector

    Parameters
    ----------
    func : Callable[_P, _RT]
        Function to decorate

    Returns
    -------
    Callable[_P, _RT]
        Decorated function
    """

    @wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _RT:
        with no_gc():
            result = func(*args, **kwargs)

        return result

    return wrapper


class DatFileMeta(NamedTuple):
    start_time: Seconds
    stop_time: Seconds
    filepath: Path
    channel_names: tuple[str, ...]
    frequency: Hz


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
    frequency : Hz
        Frequency of the signal
    """

    signal: npt.NDArray[np.float32]
    meta: DatFileMeta


def parse_float(string: str) -> float:
    return float(string.replace(",", "."))


@disable_gc
def read_dat_file(filepath: Path) -> DatFile:
    with open(filepath, "r") as input_:
        header = input_.readline()
        # ["A1(x)", "A1(y)", "A2(x)", "A2(y)"] <-- Example input
        # Strip last 3 characters to remove redundant (x) or (y)
        # Get every 2nd to remove duplicates
        # ["A1", "A2"] <-- Example output for example input above
        channel_names = tuple(
            channel_name[:-3] for channel_name in header.split()[::2]
        )

        # Read lines of floats to convert them to numpy array and transpose
        lines: list[list[float]] = []

        # Corner case for first line in purpose to get start time of the recording
        line = input_.readline().split()
        start_time: Seconds = parse_float(line[0])
        stop_time: Seconds = start_time
        prev_stop_time: Seconds = start_time
        # Get every 2nd starting with 1 to skip time columns (below the same reason)
        lines.append([parse_float(elem) for elem in line[1::2]])

        while (line := input_.readline().split()):
            lines.append([parse_float(elem) for elem in line[1::2]])
            prev_stop_time, stop_time = stop_time, parse_float(line[0])

    signal = np.array(lines, dtype=np.float32).transpose()
    frequency: Hz = round(1 / (stop_time - prev_stop_time))

    dat_file = DatFile(
        signal=signal,
        meta=DatFileMeta(
            start_time=start_time,
            stop_time=stop_time,
            filepath=filepath,
            channel_names=channel_names,
            frequency=frequency,
        ),
    )

    return dat_file
