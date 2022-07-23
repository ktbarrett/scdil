import json
import math
from typing import Iterable, Iterator, TextIO, Tuple, TypeVar

from scdil.types import SCDILMapping, SCDILSequence, SCDILValue

T = TypeVar("T")


def dump(value: SCDILValue, *, stream: TextIO) -> None:
    if value is None:
        dump_null(stream=stream)
    elif isinstance(value, bool):
        dump_bool(value, stream=stream)
    elif isinstance(value, int):
        dump_int(value, stream=stream)
    elif isinstance(value, float):
        dump_float(value, stream=stream)
    elif isinstance(value, str):
        dump_str(value, stream=stream)
    elif isinstance(value, SCDILSequence):
        dump_sequence(value, stream=stream)
    elif isinstance(value, SCDILMapping):
        dump_mapping(value, stream=stream)
    else:
        raise TypeError(f"Got unsupported type {type(value).__qualname__}")


def dump_null(*, stream: TextIO) -> None:
    stream.write("null")


def dump_bool(value: bool, *, stream: TextIO) -> None:
    if value is True:
        stream.write("true")
    elif value is False:
        stream.write("false")


def dump_int(value: int, *, stream: TextIO) -> None:
    stream.write(json.dumps(value))


def dump_float(value: float, *, stream: TextIO) -> None:
    if value is math.inf:
        stream.write("inf")
    elif value is -math.inf:
        stream.write("-inf")
    elif value is math.nan:
        stream.write("nan")
    else:
        stream.write(json.dumps(value))


def dump_line(value: str, *, stream: TextIO) -> None:
    """Prints line of data (sans terminal newline) with escaped control codes"""
    control_codes_escaped = value.encode(errors="backslashreplace").decode()
    others_escaped = control_codes_escaped.replace('"', '\\"').replace("\\", "\\\\")
    stream.write(others_escaped)


def dump_str(value: str, *, stream: TextIO) -> None:
    stream.write('"')
    dump_line(value, stream=stream)
    stream.write('"')


def dump_sequence(value: SCDILSequence, *, stream: TextIO) -> None:
    stream.write("[")
    for elem, last in mark_last(value):
        dump(elem, stream=stream)
        if not last:
            stream.write(",")
    stream.write("]")


def dump_mapping(value: SCDILMapping, *, stream: TextIO) -> None:
    stream.write("{")
    for (key, val), last in mark_last(value.items()):
        dump(key, stream=stream)
        stream.write(":")
        dump(val, stream=stream)
        if not last:
            stream.write(",")
    stream.write("}")


def mark_last(iterable: Iterable[T]) -> Iterator[Tuple[T, bool]]:
    """Returns the given iterable zipped with a boolean which is always False except on the last element"""
    it = iter(iterable)
    try:
        v = next(it)
    except StopIteration:
        return
    try:
        while True:
            prev_v = v
            v = next(it)
            yield prev_v, False
    except StopIteration:
        yield prev_v, True
