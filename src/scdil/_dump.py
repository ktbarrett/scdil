import functools
import io
import json
import math
from typing import Iterable, Iterator, TextIO, Tuple, TypeVar

from scdil._parse import is_letter
from scdil.types import SCDILMapping, SCDILSequence, SCDILValue

T = TypeVar("T")


def dumps(
    value: SCDILValue,
    *,
    for_humans: bool = True,
    indent: str = "  ",
) -> str:
    """Serializes a Python value as SCDIL to the stream"""
    string = io.StringIO()
    dump(value, string, for_humans=for_humans, indent=indent)
    return string.getvalue()


@functools.singledispatch
def dump(
    value: SCDILValue,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    """Writes a Python value in SCDIL format to the stream"""
    raise TypeError(f"Got instance of unsupported type {type(value).__qualname__!r}")


@dump.register
def _(
    value: None,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    stream.write("null")


@dump.register
def _(
    value: bool,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    if value is True:
        stream.write("true")
    elif value is False:
        stream.write("false")


@dump.register
def _(
    value: float,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    if value is math.inf:
        stream.write("inf")
    elif value is -math.inf:
        stream.write("-inf")
    elif value is math.nan:
        stream.write("nan")
    else:
        stream.write(json.dumps(value))


@dump.register
def _(
    value: int,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    stream.write(json.dumps(value))


@dump.register
def _(
    value: str,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = " ",
    _depth: int = 0,
) -> None:
    stream.write(json.dumps(value))


@dump.register
def _(
    value: SCDILSequence,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = "  ",
    _depth: int = 0,
) -> None:
    if len(value) > 0 and for_humans:
        total_indent = f"{indent * _depth}- "
        if _depth > 0:
            stream.write("\n")
        for v, last in mark_last(value):
            stream.write(total_indent)
            dump(v, stream, for_humans=for_humans, indent=indent, _depth=_depth + 1)
            if not last:
                stream.write("\n")
    else:
        stream.write("[")
        for v, last in mark_last(value):
            dump(v, stream, for_humans=for_humans)
            if not last:
                stream.write(",")
        stream.write("]")


@dump.register
def _(
    value: SCDILMapping,
    stream: TextIO,
    *,
    for_humans: bool = True,
    indent: str = "  ",
    _depth: int = 0,
) -> None:
    all_str = all(isinstance(k, str) for k in value)
    if len(value) > 0 and all_str and for_humans:
        total_indent = indent * _depth
        if _depth > 0:
            stream.write("\n")
        for (k, v), last in mark_last(value.items()):
            assert isinstance(k, str)
            stream.write(total_indent)
            dump_name(k, stream)
            stream.write(": ")
            dump(v, stream, for_humans=for_humans, indent=indent, _depth=_depth + 1)
            if not last:
                stream.write("\n")
    else:
        stream.write("{")
        for (k, v), last in mark_last(value.items()):
            dump(k, stream, for_humans=for_humans)
            stream.write(":")
            dump(v, stream, for_humans=for_humans)
            if not last:
                stream.write(",")
        stream.write("}")


def dump_name(k: str, stream: TextIO) -> None:
    if all(is_letter(c) for c in k):
        stream.write(k)
    else:
        stream.write(json.dumps(k))


def mark_last(iterable: Iterable[T]) -> Iterator[Tuple[T, bool]]:
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
