from io import StringIO
from typing import Iterable, Iterator, TextIO, Type, Union

import scdil.ast as ast
from scdil.types import SCDILValue


def load(stream: Union[str, TextIO]) -> SCDILValue:
    """Creates a Python object from SCDIL text or file"""
    if isinstance(stream, str):
        stream = StringIO(stream)
    raise NotImplementedError


class ParseError(Exception):
    ...


class Tokenizer(Iterable[ast.Token]):
    """ """

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def _next(self) -> str:
        ...

    def _lookahead(self) -> str:
        ...

    def _start_capture(self) -> None:
        ...

    def _emit(self, type: Type[ast.Token]) -> ast.Token:
        ...

    def _error(self, msg: str) -> ParseError:
        ...

    def __iter__(self) -> Iterator[ast.Token]:  # noqa: C901
        # stream starts with Indent
        yield self._emit(ast.Indent)

        c = self._next()
        while True:

            # consume insignificant whitespace
            while c in (" ", "\t"):
                c = self._next()

            self._start_capture()

            if c == "":
                break
            elif c == "\n":
                ...
            elif c in _digits:
                yield self._tok_number()
            elif c == "-":
                look = self._lookahead()
                if look in (" ", ""):
                    self._next()
                    yield self._emit(ast.Dash)
                elif look in _digits:
                    yield self._tok_number()
                else:
                    yield self._tok_name()
            elif c == "+":
                look = self._lookahead()
                if look in _digits:
                    yield self._tok_number()
                else:
                    yield self._tok_name()
            elif c == ".":
                look = self._lookahead()
                if look in _digits:
                    yield self._tok_number()
                else:
                    yield self._tok_name()
            elif c == "[":
                self._next()
                yield self._emit(ast.LBracket)
            elif c == "]":
                self._next()
                yield self._emit(ast.RBracket)
            elif c == "{":
                self._next()
                yield self._emit(ast.LCurly)
            elif c == "}":
                self._next()
                yield self._emit(ast.RCurly)
            elif c == ":":
                look = self._lookahead()
                if look == " ":
                    yield self._emit(ast.Colon)
                else:
                    yield self._tok_name()
            elif c == ",":
                self._next()
                yield self._emit(ast.Comma)
            elif c == "#":
                c = self._next()
                while c not in ("", "\n"):
                    c = self._next()
            elif c == '"':
                yield self._tok_string()
            elif c == "|":
                self._next()
                yield self._emit(ast.Pipe)
            elif c in ("~", "?"):
                look = self._lookahead()
                if c == " ":
                    raise self._error(f"Invalid name {c!r}")
                else:
                    yield self._tok_name()
            elif c in ("!", "&", "*", ">", "%", "@", "'", "`", "\\") or ord(c) < 0x20:
                raise self._error(f"Invalid character {c!r}")
            else:
                yield self._tok_name()

        # stream ends with a dedent
        yield self._emit(ast.Dedent)

    def _tok_name(self) -> ast.Name:
        ...

    def _tok_number(self) -> ast.Number:
        ...

    def _tok_string(self) -> ast.String:
        ...


_digits = frozenset("0123456789")
