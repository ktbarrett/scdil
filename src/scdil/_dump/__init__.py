import io
import sys
from typing import TextIO

from scdil._dump.human import dump as human_dump
from scdil._dump.machine import dump as machine_dump
from scdil.types import SCDILValue


def dumps(
    value: SCDILValue,
    *,
    for_humans: bool = True,
) -> str:
    """Serializes a Python value as SCDIL to the stream"""
    string = io.StringIO()
    dump(value, stream=string, for_humans=for_humans)
    return string.getvalue()


def dump(
    value: SCDILValue,
    *,
    stream: TextIO = sys.stdout,
    for_humans: bool = True,
) -> None:
    """Writes a Python value in SCDIL format to the stream"""
    if for_humans:
        human_dump(value, stream=stream)
    else:
        machine_dump(value, stream=stream)
