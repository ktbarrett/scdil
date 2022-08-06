from math import inf, nan
from typing import Dict, Iterator, List, Optional, TextIO, Type, TypeVar, Union

import scdil._ast as ast

TokenT = TypeVar("TokenT", bound=ast.Token)


class ParseError(Exception):
    def __init__(self, position: ast.Position, msg: str) -> None:
        self.position = position
        super().__init__(f"{position.lineno}:{position.charno}: {msg}")


class Parser:
    def __init__(self, stream: TextIO) -> None:
        self.lexer = Lexer(stream)
        self.curr: Optional[ast.Token] = next(self.lexer, None)
        self.lookahead: Optional[ast.Token] = None

    @property
    def position(self) -> ast.Position:
        if self.curr is None:
            return ast.Position(-1, -1)
        else:
            return self.curr.position

    def parse(self) -> ast.Node:
        if (parse := self.parse_node(None)) is None:
            raise ParseError(self.position, f"Invalid SCDIL, got {self.curr!r}")
        if self.curr is None:
            return parse
        else:
            raise ParseError(
                self.position, f"Expected end of token stream, got {self.curr!r}"
            )

    def parse_node(self, N: Optional[int]) -> Optional[ast.Node]:
        if (parse2 := self.parse_block(N)) is not None:
            return parse2
        elif (parse := self.parse_value(N)) is not None:
            return parse
        else:
            return None

    def parse_value(self, N: Optional[int]) -> Optional[ast.Value]:
        if (parse := self.parse_scalar(N)) is not None:
            return parse
        elif (parse2 := self.parse_composite(N)) is not None:
            return parse2
        else:
            return None

    def parse_scalar(self, N: Optional[int]) -> Optional[ast.Scalar]:
        if not (
            isinstance(
                value := self.curr,
                (ast.Null, ast.Boolean, ast.Integer, ast.Float, ast.String),
            )
            and check_token_N(value, N)
        ):
            return None
        _ = self.next()
        return value

    def parse_composite(self, N: Optional[int]) -> Optional[ast.Composite]:
        if (parse := self.parse_sequence(N)) is not None:
            return parse
        elif (parse2 := self.parse_mapping(N)) is not None:
            return parse2
        else:
            return None

    def parse_sequence(self, N: Optional[int]) -> Optional[ast.Sequence]:
        if not (
            isinstance(lbracket := self.curr, ast.LBracket)
            and check_token_N(lbracket, N)
        ):
            return None
        _ = self.next()
        elements: List[ast.SequenceElement] = []
        while True:
            if (element := self.parse_sequence_element()) is None:
                break
            else:
                elements.append(element)
            if element.comma is None:
                break
        if not isinstance(rbracket := self.curr, ast.RBracket):
            raise ParseError(
                self.position,
                f"Expected a ']' after last element in sequence, got {rbracket!r}",
            )
        _ = self.next()
        return ast.Sequence(lbracket, elements, rbracket)

    def parse_sequence_element(self) -> Optional[ast.SequenceElement]:
        if (value := self.parse_value(None)) is None:
            return None
        if isinstance(comma := self.curr, ast.Comma):
            _ = self.next()
        else:
            comma = None
        return ast.SequenceElement(value, comma)

    def parse_mapping(self, N: Optional[int]) -> Optional[ast.Mapping]:
        if not (
            isinstance(lcurly := self.curr, ast.LCurly) and check_token_N(lcurly, N)
        ):
            return None
        _ = self.next()
        elements: List[ast.MappingElement] = []
        while True:
            if (element := self.parse_mapping_element()) is None:
                break
            else:
                elements.append(element)
            if element.comma is None:
                break
        if not isinstance(rcurly := self.curr, ast.RCurly):
            raise ParseError(
                self.position,
                f"Expected a '}}' after last element in mapping, got {rcurly!r}",
            )
        _ = self.next()
        return ast.Mapping(lcurly, elements, rcurly)

    def parse_mapping_element(self) -> Optional[ast.MappingElement]:
        if (key := self.parse_value(None)) is None:
            return None
        if not isinstance(colon := self.curr, ast.Colon):
            raise ParseError(
                self.position,
                f"Expected a ':' after key in mapping element, got {colon!r}",
            )
        _ = self.next()
        if (value := self.parse_value(None)) is None:
            raise ParseError(
                self.position,
                f"Expected a value after ':' in mapping element, got {self.curr!r}",
            )
        if isinstance(comma := self.curr, ast.Comma):
            _ = self.next()
        else:
            comma = None
        return ast.MappingElement(key, colon, value, comma)

    def parse_block(self, N: Optional[int]) -> Optional[ast.Block]:
        if (block1 := self.parse_block_sequence(N)) is not None:
            return block1
        elif (block2 := self.parse_block_mapping(N)) is not None:
            return block2
        elif (block3 := self.parse_block_string(N)) is not None:
            return block3
        else:
            return None

    def parse_block_sequence(self, N: Optional[int]) -> Optional[ast.BlockSequence]:
        if (element := self.parse_block_sequence_element(N)) is None:
            return None
        N = element.N
        elements = [element]
        while True:
            if (element := self.parse_block_sequence_element(N)) is None:
                break
            elements.append(element)
        return ast.BlockSequence(elements)

    def parse_block_sequence_element(
        self, N: Optional[int]
    ) -> Optional[ast.BlockSequenceElement]:
        if not (isinstance(dash := self.curr, ast.Dash) and check_token_N(dash, N)):
            return None
        _ = self.next()
        if (value := self.parse_node(None)) is None:
            raise ParseError(
                self.position,
                f"Expected a value to begin block sequence element, got {self.curr!r}",
            )
        return ast.BlockSequenceElement(dash, value)

    def parse_block_mapping(self, N: Optional[int]) -> Optional[ast.BlockMapping]:
        if (element := self.parse_block_mapping_element(N)) is None:
            return None
        N = element.N
        elements = [element]
        while True:
            if (element := self.parse_block_mapping_element(N)) is None:
                break
            elements.append(element)
        return ast.BlockMapping(elements)

    def parse_block_mapping_element(
        self, N: Optional[int]
    ) -> Optional[ast.BlockMappingElement]:
        name = self.curr
        if not (
            (
                isinstance(name, ast.Name)
                or (isinstance(name, ast.String) and isinstance(self.peek(), ast.Colon))
            )
            and check_token_N(name, N)
        ):
            return None
        _ = self.next()
        if not isinstance(colon := self.curr, ast.Colon):
            raise ParseError(
                self.position,
                f"Expected a ':' after key in block mapping element, got {colon!r}",
            )
        _ = self.next()
        if (value := self.parse_node(None)) is None:
            raise ParseError(
                self.position,
                f"Expected value after ':' in block mapping element, got {self.curr!r}",
            )
        return ast.BlockMappingElement(name, colon, value)

    def parse_block_string(self, N: Optional[int]) -> Optional[ast.BlockString]:
        if (block1 := self.parse_literal_lines(N)) is not None:
            return block1
        elif (block2 := self.parse_folded_lines(N)) is not None:
            return block2
        elif (block3 := self.parse_escaped_literal_lines(N)) is not None:
            return block3
        elif (block4 := self.parse_escaped_folded_lines(N)) is not None:
            return block4
        else:
            return None

    def parse_literal_lines(self, N: Optional[int]) -> Optional[ast.LiteralLines]:
        if not (
            isinstance(line := self.curr, ast.LiteralLine) and check_token_N(line, N)
        ):
            return None
        _ = self.next()
        N = line.N
        lines = [line]
        while True:
            if not (
                isinstance(line := self.curr, ast.LiteralLine)
                and check_token_N(line, N)
            ):
                break
            lines.append(line)
            self.next()
        return ast.LiteralLines(lines)

    def parse_folded_lines(self, N: Optional[int]) -> Optional[ast.FoldedLines]:
        if not (
            isinstance(line := self.curr, ast.FoldedLine) and check_token_N(line, N)
        ):
            return None
        _ = self.next()
        N = line.N
        lines = [line]
        while True:
            if not isinstance(line := self.curr, ast.FoldedLine) or not check_token_N(
                line, N
            ):
                break
            lines.append(line)
            self.next()
        return ast.FoldedLines(lines)

    def parse_escaped_literal_lines(
        self, N: Optional[int]
    ) -> Optional[ast.EscapedLiteralLines]:
        if not (
            isinstance(line := self.curr, ast.EscapedLiteralLine)
            and check_token_N(line, N)
        ):
            return None
        _ = self.next()
        N = line.N
        lines = [line]
        while True:
            if not isinstance(
                line := self.curr, ast.EscapedLiteralLine
            ) or not check_token_N(line, N):
                break
            lines.append(line)
            self.next()
        return ast.EscapedLiteralLines(lines)

    def parse_escaped_folded_lines(
        self, N: Optional[int]
    ) -> Optional[ast.EscapedFoldedLines]:
        if not (
            isinstance(line := self.curr, ast.EscapedFoldedLine)
            and check_token_N(line, N)
        ):
            return None
        _ = self.next()
        N = line.N
        lines = [line]
        while True:
            if not (
                isinstance(line := self.curr, ast.EscapedFoldedLine)
                and check_token_N(line, N)
            ):
                break
            lines.append(line)
            self.next()
        return ast.EscapedFoldedLines(lines)

    def peek(self) -> Optional[ast.Token]:
        if self.lookahead is None:
            self.lookahead = next(self.lexer, None)
        return self.lookahead

    def next(self) -> Optional[ast.Token]:
        if self.lookahead is not None:
            self.lookahead, self.curr = None, self.lookahead
        else:
            self.curr = next(self.lexer, None)
        return self.curr


def check_token_N(token: ast.Token, N: Optional[int]) -> bool:
    if N is None:
        return True
    else:
        return token.N == N


class Lexer(Iterator[ast.Token]):
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self.lineno = 0
        self.charno = -1
        self.curr: Optional[str] = None
        self.lookahead: Optional[str] = None
        self.capture: List[str] = []

    @property
    def position(self) -> ast.Position:
        return ast.Position(self.lineno, self.charno)

    def __next__(self) -> ast.Token:  # noqa: C901
        if self.charno == -1:
            self.next()

        c = self.curr
        while True:

            # chomp whitespace
            while c in (" ", "\n"):
                c = self.next()

            # chomp comments
            if c == "#":
                while c not in ("\n", None):
                    c = self.next()

            # end of stream
            elif c is None:
                raise StopIteration

            # found something interesting
            else:
                break  # pragma: no cover

        self.start_capture()

        # null, true, false, inf, nan, names
        if is_letter(c):
            return self.lex_name()

        # numbers, +inf, -inf, dash
        elif c == "-":
            p = self.peek()
            if is_letter(p):
                return self.lex_number_special()
            elif p in (" ", "\n", "#", None):
                return self.lex_punc(ast.Dash)
            else:
                return self.lex_decimal()
        elif c == "+":
            p = self.peek()
            if is_letter(p):
                return self.lex_number_special()
            else:
                return self.lex_decimal()
        elif c == "0":
            p = self.peek()
            if p in ("X", "x"):
                return self.lex_hex()
            elif p in ("O", "o"):
                return self.lex_octal()
            elif p in ("B", "b"):
                return self.lex_binary()
            else:
                return self.lex_decimal()
        elif c in digit_chars:
            return self.lex_decimal()

        # strings
        elif c == '"':
            return self.lex_string()

        # lines
        elif c == "|":
            return self.lex_literal_line()
        elif c == ">":
            return self.lex_folded_line()
        elif c == "\\" and self.peek() == "|":
            return self.lex_escaped_literal_line()
        elif c == "\\" and self.peek() == ">":
            return self.lex_escaped_folded_line()

        # puncatuation
        elif c == "[":
            return self.lex_punc(ast.LBracket)
        elif c == "]":
            return self.lex_punc(ast.RBracket)
        elif c == "{":
            return self.lex_punc(ast.LCurly)
        elif c == "}":
            return self.lex_punc(ast.RCurly)
        elif c == ",":
            return self.lex_punc(ast.Comma)
        elif c == ":":
            return self.lex_punc(ast.Colon)

        # errors
        elif is_control_code(c):
            raise ParseError(
                self.position,
                f"Control codes are not valid source characters, got {self.curr!r}",
            )

        raise ParseError(self.position, f"Unexpected character: {self.curr!r}")

    def lex_hex(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in ("X", "x")
        c = self.next()
        if c not in hex_chars:
            raise ParseError(
                self.position, "At least one digit required in hexadecimal literal"
            )
        while c in hex_chars:
            c = self.save_and_next()
        value = int(self.get_capture(), 16)
        return ast.Integer(self.finish_capture(), value)

    def lex_octal(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in ("O", "o")
        c = self.next()
        if c not in octal_chars:
            raise ParseError(
                self.position, "At least one digit required in octal literal"
            )
        while c in octal_chars:
            c = self.save_and_next()
        value = int(self.get_capture(), 8)
        return ast.Integer(self.finish_capture(), value)

    def lex_binary(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in ("B", "b")
        c = self.next()
        if c not in ("0", "1"):
            raise ParseError(
                self.position, "At least one digit required in binary literal"
            )
        while c in ("0", "1"):
            c = self.save_and_next()
        value = int(self.get_capture(), 2)
        return ast.Integer(self.finish_capture(), value)

    def lex_decimal(self) -> Union[ast.Integer, ast.Float]:
        is_float = False
        # optional +/-
        if self.curr in ("+", "-"):
            self.save_and_next()
        # integer portion
        self.consume_integral()
        # optional fractional
        if self.curr == ".":
            is_float = True
            self.consume_fractional()
        # optional exponential
        if self.curr in ("E", "e"):
            is_float = True
            self.consume_exponent()
        # evaluate
        if is_float:
            value = float(self.get_capture())
            return ast.Float(self.finish_capture(), value)
        else:
            value = int(self.get_capture())
            return ast.Integer(self.finish_capture(), value)

    def consume_integral(self) -> None:
        c = self.curr
        if c not in digit_chars:
            raise ParseError(
                self.position,
                "At least one digit required in integral part of decimal literal",
            )
        while c in digit_chars:
            c = self.save_and_next()

    def consume_fractional(self) -> None:
        assert self.curr == "."
        c = self.save_and_next()
        while c in digit_chars:
            c = self.save_and_next()

    def consume_exponent(self) -> None:
        assert self.curr in ("E", "e")
        c = self.save_and_next()
        if c in ("+", "-"):
            c = self.save_and_next()
        if c not in digit_chars:
            raise ParseError(
                self.position,
                "At least one digit required in exponent part of decimal literal",
            )
        while c in digit_chars:
            c = self.save_and_next()

    def lex_number_special(self) -> ast.Float:
        assert self.curr in ("+", "-")
        c = self.save_and_next()
        while is_letter(c):
            c = self.save_and_next()
        value = self.get_capture()
        if value == "-inf":
            return ast.Float(self.finish_capture(), -inf)
        elif value == "+inf":
            return ast.Float(self.finish_capture(), inf)
        else:
            raise ParseError(
                self.finish_capture(), f"{value!r} is not a valid named number"
            )

    def lex_string(self) -> ast.String:
        assert self.curr == '"'
        c = self.next()
        while True:
            if c == '"':
                self.next()
                break
            elif c == "\\":
                c = self.consume_escape()
            elif is_character(c):
                c = self.save_and_next()
            elif c in ("\n", None):
                raise ParseError(self.position, "Unterminated string literal")
            elif is_control_code(c):
                raise ParseError(
                    self.position,
                    f"Control codes are not valid string characters, got {c!r}",
                )
            else:
                assert False, "unreachable"  # pragma: no cover
        return ast.String(self.finish_capture(), self.get_capture())

    def lex_literal_line(self) -> ast.LiteralLine:
        assert self.curr == "|"
        self.consume_line()
        return ast.LiteralLine(self.finish_capture(), self.get_capture())

    def lex_folded_line(self) -> ast.FoldedLine:
        assert self.curr == ">"
        self.consume_line()
        return ast.FoldedLine(self.finish_capture(), self.get_capture())

    def consume_line(self) -> None:
        c = self.next()
        while True:
            if is_character(c):
                c = self.save_and_next()
            elif c in ("\n", None):
                break
            elif is_control_code(c):
                raise ParseError(
                    self.position,
                    f"Control codes are not valid line characters, got {c!r}",
                )
            else:
                assert False, "unreachable"  # pragma: no cover

    def lex_escaped_literal_line(self) -> ast.EscapedLiteralLine:
        assert self.curr == "\\"
        assert self.next() == "|"
        self.consume_escaped_line()
        return ast.EscapedLiteralLine(self.finish_capture(), self.get_capture())

    def lex_escaped_folded_line(self) -> ast.EscapedFoldedLine:
        assert self.curr == "\\"
        assert self.next() == ">"
        self.consume_escaped_line()
        return ast.EscapedFoldedLine(self.finish_capture(), self.get_capture())

    def consume_escaped_line(self) -> None:
        c = self.next()
        while True:
            if c == "\\":
                c = self.consume_escape()
            elif is_character(c):
                c = self.save_and_next()
            elif c in ("\n", None):
                break
            elif is_control_code(c):
                raise ParseError(
                    self.position,
                    f"Control codes are not valid line characters, got {c!r}",
                )
            else:
                assert False, "unreachable"  # pragma: no cover

    def lex_name(self) -> Union[ast.Null, ast.Boolean, ast.Float, ast.Name]:
        c = self.save_and_next()
        while is_letter(c) or c in digit_chars:
            c = self.save_and_next()
        value = self.get_capture()
        if value == "null":
            return ast.Null(self.finish_capture())
        elif value == "true":
            return ast.Boolean(self.finish_capture(), True)
        elif value == "false":
            return ast.Boolean(self.finish_capture(), False)
        elif value == "inf":
            return ast.Float(self.finish_capture(), inf)
        elif value == "nan":
            return ast.Float(self.finish_capture(), nan)
        else:
            return ast.Name(self.finish_capture(), value)

    def lex_punc(self, tok_type: Type[TokenT]) -> TokenT:
        self.next()
        return tok_type(self.finish_capture())

    def consume_escape(self) -> Optional[str]:  # noqa: C901
        assert self.curr == "\\"
        c = self.next()
        try:
            escape = escape_codes[c]
        except KeyError:
            if c == "x":
                return self.consume_hex(2)
            elif c == "u":
                return self.consume_hex(4)
            elif c == "U":
                return self.consume_hex(8)
            else:
                raise ParseError(self.position, f"Invalid escape code: '\\{c}'")
        else:
            self.save(escape)
            return self.next()

    def consume_hex(self, n: int) -> Optional[str]:
        local_capture: List[str] = []
        for _ in range(n):
            c = self.next()
            if c in hex_chars:
                local_capture.append(c)
            else:
                raise ParseError(
                    self.position,
                    f"Expecting hex character as part of escape sequence, got {c!r}",
                )
        self.save(chr(int("".join(local_capture), 16)))
        return self.next()

    def _next(self) -> Optional[str]:
        c = self.stream.read(1)
        if c == "":
            return None
        else:
            return c

    def next(self) -> Optional[str]:
        if self.curr == "\n":
            self.lineno += 1
            self.charno = 0
        else:
            self.charno += 1
        if self.lookahead is None:
            self.curr = self._next()
        else:
            self.curr, self.lookahead = self.lookahead, None
        return self.curr

    def peek(self) -> Optional[str]:
        if self.lookahead is None:
            c = self.stream.read(1)
            if c == "":
                self.lookahead = None
            else:
                self.lookahead = c
        return self.lookahead

    def save(self, c: str) -> None:
        self.capture.append(c)

    def save_and_next(self) -> Optional[str]:
        assert self.curr is not None
        self.save(self.curr)
        return self.next()

    def start_capture(self) -> None:
        self.start_lineno = self.lineno
        self.start_charno = self.charno
        self.capture.clear()

    def finish_capture(self) -> ast.Position:
        return ast.Position(self.start_lineno, self.start_charno)

    def get_capture(self) -> str:
        return "".join(self.capture)


escape_codes: Dict[Optional[str], str] = {
    "\\": "\\",
    '"': '"',
    "/": "/",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
}
octal_chars = frozenset("01234567")
digit_chars = frozenset("0123456789")
hex_chars = frozenset("0123456789abcdefABCDEF")


def is_letter(c: Optional[str]) -> bool:
    return c is not None and (
        c in "_" or "a" <= c <= "z" or "A" <= c <= "Z" or c >= "\xA0"
    )


def is_character(c: Optional[str]) -> bool:
    return c is not None and ("\x20" <= c < "\x7F" or c >= "\xA0")


def is_control_code(c: Optional[str]) -> bool:
    return c is not None and ("\x00" <= c < "\x20" or "\x7F" <= c < "\xA0")
