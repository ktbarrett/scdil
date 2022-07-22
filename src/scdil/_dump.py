import io
import json
import math
import sys
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Iterable, Iterator, Literal, TextIO, Tuple, TypeVar, overload

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
    dump(value, stream=string, for_humans=for_humans, indent=indent)
    return string.getvalue()


def dump(
    value: SCDILValue,
    *,
    stream: TextIO = sys.stdout,
    for_humans: bool = True,
    indent: str = "  ",
) -> None:
    """Writes a Python value in SCDIL format to the stream"""
    if for_humans:
        HumanDumper(stream=stream, indent=indent).dump(value)
    else:
        MachineDumper(stream=stream).dump(value)


class DumperBase(ABC):
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def dump(self, value: SCDILValue) -> None:
        if value is None:
            self.dump_null()
        elif isinstance(value, bool):
            self.dump_bool(value)
        elif isinstance(value, int):
            self.dump_int(value)
        elif isinstance(value, float):
            self.dump_float(value)
        elif isinstance(value, str):
            self.dump_str(value)
        elif isinstance(value, SCDILSequence):
            self.dump_sequence(value)
        elif isinstance(value, SCDILMapping):
            self.dump_mapping(value)
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")

    def dump_null(self) -> None:
        self.stream.write("null")

    def dump_bool(self, value: bool) -> None:
        if value is True:
            self.stream.write("true")
        elif value is False:
            self.stream.write("false")

    def dump_int(self, value: int) -> None:
        self.stream.write(json.dumps(value))

    def dump_float(self, value: float) -> None:
        if value is math.inf:
            self.stream.write("inf")
        elif value is -math.inf:
            self.stream.write("-inf")
        elif value is math.nan:
            self.stream.write("nan")
        else:
            self.stream.write(json.dumps(value))

    @abstractmethod
    def dump_str(self, value: str, depth: int) -> None:
        ...

    @abstractmethod
    def dump_sequence(self, value: SCDILSequence, depth: int) -> None:
        ...

    @abstractmethod
    def dump_mapping(self, mapping: SCDILMapping, depth: int) -> None:
        ...


class HumanDumper(DumperBase):
    def __init__(self, stream: TextIO, indent: str) -> None:
        super().__init__(stream, indent)
        self.block_context: bool = True

    @contextmanager
    def leave_block_context(self) -> None:
        self.block_context = False
        yield
        self.block_context = True

    def dump_str(self, value: str, depth: int) -> None:
        if self.block_context and "\n" in value:
            self.dump_block_str(value, depth)
        else:
            self.dump_nonblock_str(value)

    def dump_block_str(self, s: str, depth: int) -> None:
        line_start = self.indent * depth + "|"
        for line, last in mark_last(s.splitlines()):
            self.stream.write(line_start)
            self.dump_line(line)
            if not last:
                self.stream.write("\n")

    def dump_nonblock_str(self, s: str) -> None:
        self.stream.write('"')
        self.dump_line(s)
        self.stream.write('"')

    def dump_line(self, s: str) -> None:
        """Prints line of data (sans terminal newline) with escaped control codes"""
        control_codes_escaped = s.encode(errors="backslashreplace").decode()
        others_escaped = control_codes_escaped.replace('"', '\\"').replace("\\", "\\\\")
        self.stream.write(others_escaped)

    def dump_sequence(self, value: SCDILSequence, depth: int) -> None:
        if self.block_context:
            self.dump_block_sequence(value, depth)
        else:
            self.dump_nonblock_sequence(value, depth)

    def dump_block_sequence(self, value: SCDILSequence, depth: int) -> None:
        """Prints sequence in block format"""
        if len(value) == 0:
            self.stream.write("[]")
            return
        self.stream.write("\n")
        line_start = self.indent * depth + "- "
        for elem, last in mark_last(value):
            self.stream.write(line_start)
            self.dump(elem, depth + 1)
            if not last:
                self.stream.write("\n")

    def dump_nonblock_sequence(self, value: SCDILSequence, depth: int) -> None:
        """Pretty prints sequence"""
        if len(value) == 0:
            self.stream.write("[]")
            return
        self.stream.write("[\n")
        line_start = self.indent * (depth + 1)
        for elem in value:
            self.stream.write(line_start)
            self.dump(elem, depth + 1)
            self.stream.write(",\n")
        self.stream.write(self.indent * depth)
        self.stream.write("]")

    def dump_mapping(self, mapping: SCDILMapping, depth) -> None:
        if self.block_context and all(isinstance(key, str) for key in mapping.keys()):
            self.dump_block_mapping(mapping, depth)
        else:
            self.dump_nonblock_mapping(mapping, depth)

    def dump_block_mapping(self, mapping: SCDILMapping, depth: int) -> None:
        """Prints mapping in block format"""
        if len(mapping) == 0:
            self.stream.write("{}")
            return
        line_start = self.indent * depth
        for (key, value), last in mark_last(mapping.items()):
            self.stream.write(line_start)
            with self.leave_block_context():
                self.dump(key, depth + 1)
            self.stream.write(": ")
            self.dump(value, depth + 1)
            if not last:
                self.stream.write("\n")

    def dump_nonblock_mapping(self, mapping: SCDILMapping, depth: int) -> None:
        """Pretty prints mapping"""
        if len(mapping) == 0:
            self.stream.write("{}")
            return
        self.stream.write("{\n")
        line_start = self.indent * (depth + 1)
        for key, value in mapping.items():
            self.stream.write(line_start)
            self.dump(key, depth + 1)
            self.stream.write(": ")
            self.dump(value, depth + 1)
            self.stream.write(", ")
        self.stream.write(self.indent * depth)
        self.stream.write("}")


class MachineDumper(DumperBase):
    def dump_str(self, s: str) -> None:
        self.stream.write('"')
        self.dump_line(s)
        self.stream.write('"')

    def dump_sequence(self, value: SCDILSequence) -> None:
        self.stream.write("[")
        for elem, last in mark_last(value):
            self.dump(elem)
            if not last:
                self.stream.write(",")
        self.stream.write("]")

    def dump_mapping(self, mapping: SCDILMapping) -> None:
        self.stream.write("{")
        for (key, value), last in mark_last(mapping.items()):
            self.dump(key)
            self.stream.write(":")
            self.dump(value)
            if not last:
                self.stream.write(",")
        self.stream.write("}")


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
