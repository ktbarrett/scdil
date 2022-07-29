import io
import json
import math
import sys
from abc import ABC, abstractmethod
from typing import Iterable, Iterator, Set, TextIO, Tuple, TypeVar, cast

from scdil._types import Mapping, Sequence, Value

T = TypeVar("T")


def dumps(
    value: Value,
    *,
    for_humans: bool = True,
) -> str:
    """Dumps a Python value as a SCDIL string"""
    string = io.StringIO()
    dump(value, stream=string, for_humans=for_humans)
    return string.getvalue()


def dump(
    value: Value,
    *,
    stream: TextIO = sys.stdout,
    for_humans: bool = True,
) -> None:
    """Dumps a Python value in SCDIL format to the stream"""
    if for_humans:
        HumanDumper(stream=stream).dump(value)
    else:
        MachineDumper(stream=stream).dump(value)


literal_string_escaper = {i: f"\\x{i:02X}" for i in range(32)}  # C0 control codes
literal_string_escaper.update(
    {i: f"\\x{i:02X}" for i in range(127, 160)}
)  # DEL and C1 control codes
# special cases
literal_string_escaper[ord("\n")] = "\\n"
literal_string_escaper[ord("\r")] = "\\r"
literal_string_escaper[ord("\t")] = "\\t"
literal_string_escaper[ord("\\")] = "\\\\"
literal_string_escaper[ord('"')] = '\\"'
# we do not do special translation for \b, \f, \v, and \/, because they need to die

escaped_block_string_escaper = literal_string_escaper.copy()
del escaped_block_string_escaper[ord('"')]

_use_escape_code = {chr(c) for c in literal_string_escaper}
_use_escape_code.remove("\n")


def needs_escaping(value: str) -> bool:
    return bool(_use_escape_code.intersection(value))


class DumperBase(ABC):
    @property
    def stream(self) -> TextIO:
        return self._stream

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._seen: Set[int] = set()

    def check_recursive(self, value: Value) -> None:
        if id(value) in self._seen:
            raise ValueError(
                f"Object {object.__repr__(value)} is recursive, aborting dump"
            )
        self._seen.add(id(value))

    def dump_null(self) -> None:
        self.stream.write("null")

    def dump_bool(self, value: bool) -> None:
        if value is True:
            self.stream.write("true")
        elif value is False:
            self.stream.write("false")
        else:  # pragma: no cover
            assert False, f"Got abnormal bool {value!r}"

    def dump_int(self, value: int) -> None:
        self.stream.write(json.dumps(value))

    def dump_float(self, value: float) -> None:
        if value == math.inf:
            self.stream.write("inf")
        elif value == -math.inf:
            self.stream.write("-inf")
        elif math.isnan(value):
            self.stream.write("nan")
        else:
            self.stream.write(json.dumps(value))

    def dump_str(self, value: str) -> None:
        self.stream.write('"')
        self.dump_literal_line(value)
        self.stream.write('"')

    def dump_literal_line(self, value: str) -> None:
        self.stream.write(value.translate(literal_string_escaper))

    @abstractmethod
    def dump(self, value: Value) -> None:
        ...


class MachineDumper(DumperBase):
    def dump(self, value: Value) -> None:
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
        elif isinstance(value, Sequence):
            self.dump_sequence(value)
        elif isinstance(value, Mapping):
            self.dump_mapping(value)
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")

    def dump_sequence(self, value: Sequence) -> None:
        self.check_recursive(value)
        self.stream.write("[")
        for elem, last in mark_last(value):
            self.dump(elem)
            if not last:
                self.stream.write(",")
        self.stream.write("]")

    def dump_mapping(self, value: Mapping) -> None:
        self.check_recursive(value)
        self.stream.write("{")
        for (key, val), last in mark_last(value.items()):
            self.dump(key)
            self.stream.write(":")
            self.dump(val)
            if not last:
                self.stream.write(",")
        self.stream.write("}")


class HumanDumper(DumperBase):
    def dump(self, value: Value) -> None:  # noqa: C901
        if value is None:
            self.dump_null()
        elif isinstance(value, bool):
            self.dump_bool(value)
        elif isinstance(value, int):
            self.dump_int(value)
        elif isinstance(value, float):
            self.dump_float(value)
        elif isinstance(value, str):
            if value == "\n":
                self.stream.write('"\\n"')
            elif "\n" in value:
                if needs_escaping(value):
                    self.dump_escaped_block_string(value, depth=0)
                else:
                    self.dump_block_string(value, depth=0)
            else:
                self.dump_str(value)
        elif isinstance(value, Sequence):
            if len(value) == 0:
                self.stream.write("[]")
            else:
                self.dump_block_sequence(value, depth=0)
        elif isinstance(value, Mapping):
            if len(value) == 0:
                self.stream.write("{}")
            elif all(isinstance(key, str) for key in value.keys()):
                self.dump_block_mapping(value, depth=0)
            else:
                self.dump_literal_mapping(value, depth=0)
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")
        # always end the dump with a newline
        self.stream.write("\n")

    def dispatch_literal(self, value: Value, depth: int) -> None:  # noqa: C901
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
        elif isinstance(value, Sequence):
            if len(value) == 0:
                self.stream.write("[]")
            else:
                self.dump_literal_sequence(value, depth=depth)
        elif isinstance(value, Mapping):
            if len(value) == 0:
                self.stream.write("{}")
            else:
                self.dump_literal_mapping(value, depth=depth)
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")

    def dump_literal_sequence(self, value: Sequence, depth: int) -> None:
        self.check_recursive(value)
        self.stream.write("[\n")
        line_start = "  " * (depth + 1)
        for elem, last in mark_last(value):
            self.stream.write(line_start)
            self.dispatch_literal(elem, depth=(depth + 1))
            if not last:
                self.stream.write(",")
            self.stream.write("\n")
        self.stream.write("  " * depth)
        self.stream.write("]")

    def dump_literal_mapping(self, value: Mapping, depth: int) -> None:
        self.check_recursive(value)
        self.stream.write("{\n")
        line_start = "  " * (depth + 1)
        for (key, val), last in mark_last(value.items()):
            self.stream.write(line_start)
            self.dispatch_literal(key, depth=(depth + 1))
            self.stream.write(": ")
            self.dispatch_literal(val, depth=(depth + 1))
            if not last:
                self.stream.write(",")
            self.stream.write("\n")
        self.stream.write("  " * depth)
        self.stream.write("}")

    def dump_block_string(self, value: str, depth: int) -> None:
        next_line = "\n" + "  " * depth
        for line, last in mark_last(value.split("\n")):
            self.stream.write("|")
            # normally this would escape control code
            # but we have already checked that value has no escape codes before calling this function
            self.dump_literal_line(line)
            if not last:
                self.stream.write(next_line)

    def dump_escaped_block_string(self, value: str, depth: int) -> None:
        next_line = "\n" + "  " * depth
        for line, last in mark_last(value.split("\n")):
            self.stream.write("\\|")
            self.dump_escaped_block_line(line)
            if not last:
                self.stream.write(next_line)

    def dump_escaped_block_line(self, value: str) -> None:
        self.stream.write(value.translate(escaped_block_string_escaper))

    def dump_block_sequence(self, value: Sequence, depth: int) -> None:
        self.check_recursive(value)
        next_line = "\n" + "  " * depth
        for elem, last in mark_last(value):
            self.stream.write("-")
            self.dispatch_block_sequence_elem(elem, depth=depth)
            if not last:
                self.stream.write(next_line)

    def dispatch_block_sequence_elem(  # noqa: C901
        self, value: Value, depth: int
    ) -> None:
        if value is None:
            self.stream.write(" ")
            self.dump_null()
        elif isinstance(value, bool):
            self.stream.write(" ")
            self.dump_bool(value)
        elif isinstance(value, int):
            self.stream.write(" ")
            self.dump_int(value)
        elif isinstance(value, float):
            self.stream.write(" ")
            self.dump_float(value)
        elif isinstance(value, str):
            if value == "\n":
                self.stream.write(' "\\n"')
            elif "\n" in value:
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                if needs_escaping(value):
                    self.dump_escaped_block_string(value, depth=(depth + 1))
                else:
                    self.dump_block_string(value, depth=(depth + 1))
            else:
                self.stream.write(" ")
                self.dump_str(value)
        elif isinstance(value, Sequence):
            if len(value) == 0:
                self.stream.write(" []")
            else:
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                self.dump_block_sequence(value, depth=(depth + 1))
        elif isinstance(value, Mapping):
            if len(value) == 0:
                self.stream.write(" {}")
            elif all(isinstance(key, str) for key in value.keys()):
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                self.dump_block_mapping(value, depth=(depth + 1))
            else:
                self.stream.write(" ")
                self.dump_literal_mapping(value, depth=(depth + 1))
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")

    def dump_block_mapping(self, value: Mapping, depth: int) -> None:
        self.check_recursive(value)
        next_line = "\n" + "  " * depth
        for (key, val), last in mark_last(value.items()):
            key = cast(str, key)
            self.dump_block_mapping_key(key)
            self.stream.write(":")
            self.dispatch_block_mapping_value(val, depth=depth)
            if not last:
                self.stream.write(next_line)

    def dump_block_mapping_key(self, value: str) -> None:
        # TODO: this check may be more or less forgiving than parser
        if value.isidentifier():
            self.stream.write(value)
        else:
            self.dump_str(value)

    def dispatch_block_mapping_value(  # noqa: C901
        self, value: Value, depth: int
    ) -> None:
        if value is None:
            self.stream.write(" ")
            self.dump_null()
        elif isinstance(value, bool):
            self.stream.write(" ")
            self.dump_bool(value)
        elif isinstance(value, int):
            self.stream.write(" ")
            self.dump_int(value)
        elif isinstance(value, float):
            self.stream.write(" ")
            self.dump_float(value)
        elif isinstance(value, str):
            if value == "\n":
                self.stream.write(' "\\n"')
            elif "\n" in value:
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                if needs_escaping(value):
                    self.dump_escaped_block_string(value, depth=(depth + 1))
                else:
                    self.dump_block_string(value, depth=(depth + 1))
            else:
                self.stream.write(" ")
                self.dump_str(value)
        elif isinstance(value, Sequence):
            if len(value) == 0:
                self.stream.write(" []")
            else:
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                self.dump_block_sequence(value, depth=(depth + 1))
        elif isinstance(value, Mapping):
            if len(value) == 0:
                self.stream.write(" {}")
            elif all(isinstance(key, str) for key in value.keys()):
                self.stream.write("\n")
                self.stream.write("  " * (depth + 1))
                self.dump_block_mapping(value, depth=(depth + 1))
            else:
                self.stream.write(" ")
                self.dump_literal_mapping(value, depth=(depth + 1))
        else:
            raise TypeError(f"Got unsupported type {type(value).__qualname__}")


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
