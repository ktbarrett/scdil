import functools
import io
import json
import math
from typing import Iterable, Iterator, List, TextIO, Tuple, TypeVar

from scdil._parse import is_letter
from scdil.types import SCDILMapping, SCDILSequence, SCDILValue

T = TypeVar("T")


def dumps(
    value: SCDILValue,
    *,
    for_humans: bool = True,
    indent: str = "  ",
    escape_unicode: bool = False,
) -> str:
    """Serializes a Python value as SCDIL to the stream"""
    string = io.StringIO()
    Dumper(
        stream=string,
        for_humans=for_humans,
        indent=indent,
        escape_unicode=escape_unicode,
    ).dump(value, 0)
    return string.getvalue()


@functools.singledispatch
def dump(
    value: SCDILValue,
    *,
    stream: TextIO,
    for_humans: bool = True,
    indent: str = "  ",
    escape_unicode: bool = False,
) -> None:
    """Writes a Python value in SCDIL format to the stream"""
    Dumper(
        stream=stream,
        for_humans=for_humans,
        indent=indent,
        escape_unicode=escape_unicode,
    ).dump(value, 0)
    stream.write("\n")


class Dumper:
    def __init__(
        self, stream: TextIO, for_humans: bool, indent: str, escape_unicode: bool
    ) -> None:
        self.stream = stream
        self.for_humans = for_humans
        self.indent = indent
        self.escape_unicode = escape_unicode
        self.stack: List[int] = []

    @functools.singledispatchmethod
    def dump(self, value: SCDILValue, depth: int) -> None:
        raise TypeError(
            f"Got instance of unsupported type {type(value).__qualname__!r}"
        )

    @dump.register
    def _(
        self,
        value: None,
        depth: int,
    ) -> None:
        self.stream.write("null")

    @dump.register
    def _(
        self,
        value: bool,
        depth: int,
    ) -> None:
        if value is True:
            self.stream.write("true")
        elif value is False:
            self.stream.write("false")

    @dump.register
    def _(
        self,
        value: float,
        depth: int,
    ) -> None:
        if value is math.inf:
            self.stream.write("inf")
        elif value is -math.inf:
            self.stream.write("-inf")
        elif value is math.nan:
            self.stream.write("nan")
        else:
            self.stream.write(json.dumps(value))

    @dump.register
    def _(
        self,
        value: int,
        depth: int,
    ) -> None:
        self.stream.write(json.dumps(value))

    @dump.register
    def _(
        self,
        value: str,
        depth: int,
    ) -> None:
        self.stream.write(json.dumps(value))

    @dump.register
    def _(
        self,
        value: SCDILSequence,
        depth: int,
    ) -> None:
        if id(value) in self.stack:
            raise ValueError("Can't dump recursive value")
        else:
            self.stack.append(id(value))
        if len(value) > 0 and self.for_humans:
            total_indent = f"{self.indent * depth}- "
            if depth > 0:
                self.stream.write("\n")
            for v, last in mark_last(value):
                self.stream.write(total_indent)
                self.dump(v, depth=depth + 1)
                if not last:
                    self.stream.write("\n")
        else:
            self.stream.write("[")
            for v, last in mark_last(value):
                self.dump(v, depth=depth + 1)
                if not last:
                    self.stream.write(",")
            self.stream.write("]")
        self.stack.pop()

    @dump.register
    def _(
        self,
        value: SCDILMapping,
        depth: int,
    ) -> None:
        if id(value) in self.stack:
            raise ValueError("Can't dump recursive value")
        else:
            self.stack.append(id(value))
        all_str = all(isinstance(k, str) for k in value)
        if len(value) > 0 and all_str and self.for_humans:
            total_indent = self.indent * depth
            if depth > 0:
                self.stream.write("\n")
            for (k, v), last in mark_last(value.items()):
                assert isinstance(k, str)
                self.stream.write(total_indent)
                self.dump_name(k, depth=depth + 1)
                self.stream.write(": ")
                self.dump(v, depth=depth + 1)
                if not last:
                    self.stream.write("\n")
        else:
            self.stream.write("{")
            for (k, v), last in mark_last(value.items()):
                self.dump(k, depth=depth + 1)
                self.stream.write(":")
                self.dump(v, depth=depth + 1)
                if not last:
                    self.stream.write(",")
            self.stream.write("}")
        self.stack.pop()

    def dump_name(self, k: str, depth: int) -> None:
        if all(is_letter(c) for c in k):
            self.stream.write(k)
        else:
            self.stream.write(json.dumps(k))


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
