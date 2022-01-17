from math import inf, nan
from typing import Iterator, List, Optional, TextIO, Type, TypeVar, Union

import scdil._ast as ast

TokenT = TypeVar("TokenT", bound=ast.Token)


class ParseError(Exception):
    ...


class Parser:
    def __init__(self, stream: TextIO) -> None:
        self.lexer = Lexer(stream)
        self.lookahead: Optional[ast.Token] = None

    def parse(self) -> Optional[ast.Node]:
        if (parse := self.parse_node(None)) is not None:
            if self.peek_tok() is None:
                return parse
            else:
                raise ParseError("Expected end of end of token stream")
        else:
            return None

    def parse_node(self, N: Optional[int]) -> Optional[ast.Node]:
        if (parse := self.parse_value(N)) is not None:
            return parse
        elif (parse2 := self.parse_block(N)) is not None:
            return parse2
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
        value = self.peek_tok()
        if isinstance(
            value, (ast.Null, ast.Boolean, ast.Integer, ast.Float, ast.String)
        ) and self.check_N(value, N):
            _ = self.next_tok()
            return ast.Scalar(value)
        else:
            return None

    def parse_composite(self, N: Optional[int]) -> Optional[ast.Composite]:
        if (parse := self.parse_sequence(N)) is not None:
            return parse
        elif (parse2 := self.parse_mapping(N)) is not None:
            return parse2
        else:
            return None

    def parse_sequence(self, N: Optional[int]) -> Optional[ast.Sequence]:
        if isinstance(lbracket := self.peek_tok(), ast.LBracket) and self.check_N(
            lbracket, N
        ):
            _ = self.next_tok()
            elements: List[ast.SequenceElement] = []
            while True:
                if (element := self.parse_sequence_element()) is None:
                    break
                else:
                    elements.append(element)
                if element.comma is None:
                    break
            if not isinstance(rbracket := self.next_tok(), ast.RBracket):
                raise ParseError(...)
            else:
                return ast.Sequence(lbracket, elements, rbracket)
        else:
            return None

    def parse_sequence_element(self) -> Optional[ast.SequenceElement]:
        if (value := self.parse_value(None)) is None:
            return None
        if isinstance(comma := self.peek_tok(), ast.Comma):
            _ = self.next_tok()
        else:
            comma = None
        return ast.SequenceElement(
            value=value,
            comma=comma,
        )

    def parse_mapping(self, N: Optional[int]) -> Optional[ast.Mapping]:
        if isinstance(lcurly := self.peek_tok(), ast.LCurly) and self.check_N(
            lcurly, N
        ):
            _ = self.next_tok()
            elements: List[ast.MappingElement] = []
            while True:
                if (element := self.parse_mapping_element()) is None:
                    break
                else:
                    elements.append(element)
                if element.comma is None:
                    break
            if not isinstance(rcurly := self.next_tok(), ast.RCurly):
                raise ParseError(...)
            else:
                return ast.Mapping(lcurly, elements, rcurly)
        else:
            return None

    def parse_mapping_element(self) -> Optional[ast.MappingElement]:
        if (key := self.parse_value(None)) is None:
            return None
        if not isinstance(colon := self.next_tok(), ast.Colon):
            raise ParseError(...)
        if (value := self.parse_value(None)) is None:
            raise ParseError(...)
        if isinstance(comma := self.peek_tok(), ast.Comma):
            _ = self.next_tok()
        else:
            comma = None
        return ast.MappingElement(
            key=key,
            colon=colon,
            value=value,
            comma=comma,
        )

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
        if (element := self.parse_block_sequence_element(N)) is not None:
            N = element.N
            elements = [element]
            while True:
                if (element := self.parse_block_sequence_element(N)) is None:
                    break
                elements.append(element)
            return ast.BlockSequence(elements)
        else:
            return None

    def parse_block_sequence_element(
        self, N: Optional[int]
    ) -> Optional[ast.BlockSequenceElement]:
        if isinstance(dash := self.peek_tok(), ast.Dash) and self.check_N(dash, N):
            _ = self.next_tok()
            if (node := self.parse_node(None)) is None:
                raise ParseError(...)
            return ast.BlockSequenceElement(dash, node)
        else:
            return None

    def parse_block_mapping(self, N: Optional[int]) -> Optional[ast.BlockMapping]:
        if (element := self.parse_block_mapping_element(N)) is not None:
            N = element.N
            elements = [element]
            while True:
                if (element := self.parse_block_mapping_element(N)) is None:
                    break
                elements.append(element)
            return ast.BlockMapping(elements)
        else:
            return None

    def parse_block_mapping_element(
        self, N: Optional[int]
    ) -> Optional[ast.BlockMappingElement]:
        if isinstance(name := self.peek_tok(), (ast.Name, ast.String)) and self.check_N(
            name, N
        ):
            _ = self.next_tok()
            if not isinstance(colon := self.next_tok(), ast.Colon):
                raise ParseError(...)
            if (node := self.parse_node(None)) is None:
                raise ParseError(...)
            return ast.BlockMappingElement(name, colon, node)
        else:
            return None

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
        if isinstance(line := self.peek_tok(), ast.LiteralLine) and self.check_N(
            line, N
        ):
            _ = self.next_tok()
            N = self.get_N(line)
            lines = [line]
            while True:
                if not isinstance(
                    line := self.peek_tok(), ast.LiteralLine
                ) or not self.check_N(line, N):
                    break
                lines.append(line)
            return ast.LiteralLines(lines)
        else:
            return None

    def parse_folded_lines(self, N: Optional[int]) -> Optional[ast.FoldedLines]:
        if isinstance(line := self.peek_tok(), ast.FoldedLine) and self.check_N(
            line, N
        ):
            _ = self.next_tok()
            N = self.get_N(line)
            lines = [line]
            while True:
                if not isinstance(
                    line := self.peek_tok(), ast.FoldedLine
                ) or not self.check_N(line, N):
                    break
                lines.append(line)
            return ast.FoldedLines(lines)
        else:
            return None

    def parse_escaped_literal_lines(
        self, N: Optional[int]
    ) -> Optional[ast.EscapedLiteralLines]:
        if isinstance(line := self.peek_tok(), ast.EscapedLiteralLine) and self.check_N(
            line, N
        ):
            _ = self.next_tok()
            N = self.get_N(line)
            lines = [line]
            while True:
                if not isinstance(
                    line := self.peek_tok(), ast.EscapedLiteralLine
                ) or not self.check_N(line, N):
                    break
                lines.append(line)
            return ast.EscapedLiteralLines(lines)
        else:
            return None

    def parse_escaped_folded_lines(
        self, N: Optional[int]
    ) -> Optional[ast.EscapedFoldedLines]:
        if isinstance(line := self.peek_tok(), ast.EscapedFoldedLine) and self.check_N(
            line, N
        ):
            _ = self.next_tok()
            N = self.get_N(line)
            lines = [line]
            while True:
                if not isinstance(
                    line := self.peek_tok(), ast.EscapedFoldedLine
                ) or not self.check_N(line, N):
                    break
                lines.append(line)
            return ast.EscapedFoldedLines(lines)
        else:
            return None

    def peek_tok(self) -> Optional[ast.Token]:
        if self.lookahead is None:
            self.lookahead = next(self.lexer, None)
        return self.lookahead

    def next_tok(self) -> Optional[ast.Token]:
        if self.lookahead is not None:
            self.lookahead, res = None, self.lookahead
            return res
        else:
            return next(self.lexer, None)

    @staticmethod
    def get_N(token: ast.Token) -> int:
        return token.position.charno

    @staticmethod
    def check_N(token: ast.Token, N: Optional[int]) -> bool:
        return N is not None and Parser.get_N(token) == N


class Lexer(Iterator[ast.Token]):
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self.lineno = 0
        self.charno = -1
        self.curr = ""
        self.lookahead: Optional[str] = None
        self.capture: List[str] = []

    def __next__(self) -> ast.Token:  # noqa: C901
        if self.charno == -1:
            self.next()

        while True:
            c = self.curr

            # chomp whitespace
            while c in " \n":
                c = self.next()

            # chomp comments
            if c == "#":
                while c != "\n":
                    c = self.next()
                continue

            # found something interesting
            self.start_capture()

            # null, true, false, inf, nan, names
            if self.is_letter(c):
                return self.lex_name()

            # numbers, +inf, -inf, dash
            elif c == "-":
                p = self.peek()
                if self.is_letter(p):
                    return self.lex_number_special()
                elif self.is_digit(p):
                    return self.lex_decimal()
                else:
                    return self.lex_punc(ast.Dash)
            elif c == "+":
                p = self.peek()
                if self.is_letter(p):
                    return self.lex_number_special()
                elif self.is_digit(p):
                    return self.lex_decimal()
                # fallthough to ParseError
            elif c == "0":
                p = self.peek()
                if p in "Xx":
                    return self.lex_hex()
                elif p in "Oo":
                    return self.lex_octal()
                elif p in "Bb":
                    return self.lex_binary()
                else:
                    return self.lex_decimal()
            elif c in "123456789":
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

            # end of stream
            elif c == "":
                raise StopIteration

            raise ParseError(...)

    def lex_hex(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in "Xx"
        c = self.next()
        if not self.is_hex(c):
            raise ParseError(...)
        while self.is_hex(c):
            c = self.save_and_next()
        value = int(self.get_capture(), 16)
        return ast.Integer(self.finish_capture(), value)

    def lex_octal(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in "Oo"
        c = self.next()
        if c not in "01234567":
            raise ParseError(...)
        while c in "01234567":
            c = self.save_and_next()
        value = int(self.get_capture(), 8)
        return ast.Integer(self.finish_capture(), value)

    def lex_binary(self) -> ast.Integer:
        assert self.curr == "0"
        c = self.next()
        assert c in "Bb"
        c = self.next()
        if c not in "01":
            raise ParseError(...)
        while c in "01":
            c = self.save_and_next()
        value = int(self.get_capture(), 2)
        return ast.Integer(self.finish_capture(), value)

    def lex_decimal(self) -> Union[ast.Integer, ast.Float]:
        is_float = False
        # optional +/-
        if self.curr in "+-":
            self.save_and_next()
        # integer portion
        self.consume_integral()
        # optional fractional
        if self.curr == ".":
            is_float = True
            self.consume_fractional()
        # optional exponential
        if self.curr in "Ee":
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
        if not self.is_digit(c):
            raise ParseError(...)
        while self.is_digit(c):
            c = self.save_and_next()

    def consume_fractional(self) -> None:
        assert self.curr == "."
        c = self.save_and_next()
        while self.is_digit(c):
            c = self.save_and_next()

    def consume_exponent(self) -> None:
        assert self.curr in "Ee"
        c = self.save_and_next()
        if c in "+-":
            c = self.save_and_next()
        if not self.is_digit(c):
            raise ParseError(...)
        while self.is_digit(c):
            c = self.save_and_next()

    def lex_number_special(self) -> ast.Float:
        c = self.curr
        while self.is_letter(c):
            c = self.save_and_next()
        value = self.get_capture()
        if value == "-inf":
            return ast.Float(self.finish_capture(), value=-inf)
        elif value == "+inf":
            return ast.Float(self.finish_capture(), value=inf)
        else:
            raise ParseError(...)

    def lex_string(self) -> ast.String:
        c = self.next()
        while True:
            if c == '"':
                self.next()
                break
            elif c == "\\":
                self.consume_escape()
            elif self.is_character(c):
                self.save_and_next()
            elif c in ("\n", ""):
                raise ParseError(...)
            elif self.is_control_code(c):
                raise ParseError(...)
            else:
                assert False, "unreachable"
        return ast.String(self.finish_capture(), self.get_capture())

    def lex_literal_line(self) -> ast.LiteralLine:
        c = self.next()
        while True:
            if self.is_character(c):
                c = self.save_and_next()
            elif c in ("\n", ""):
                break
            elif self.is_control_code(c):
                raise ParseError(...)
            else:
                assert False, "unreachable"
        return ast.LiteralLine(self.finish_capture(), self.get_capture())

    def lex_folded_line(self) -> ast.FoldedLine:
        c = self.next()
        while True:
            if self.is_character(c):
                c = self.save_and_next()
            elif c in ("\n", ""):
                break
            elif self.is_control_code(c):
                raise ParseError(...)
            else:
                assert False, "unreachable"
        value = self.get_capture().strip()
        if value == "":
            value = "\n"
        else:
            value += " "
        return ast.FoldedLine(self.finish_capture(), value)

    def lex_escaped_literal_line(self) -> ast.EscapedLiteralLine:
        c = self.next()
        while True:
            if c == "\\":
                self.consume_escape()
            elif self.is_character(c):
                c = self.save_and_next()
            elif c in ("\n", ""):
                break
            elif self.is_control_code(c):
                raise ParseError(...)
            else:
                assert False, "unreachable"
        return ast.EscapedLiteralLine(self.finish_capture(), self.get_capture())

    def lex_escaped_folded_line(self) -> ast.EscapedFoldedLine:
        c = self.next()
        while True:
            if c == "\\":
                self.consume_escape()
            elif self.is_character(c):
                c = self.save_and_next()
            elif c in ("\n", ""):
                break
            elif self.is_control_code(c):
                raise ParseError(...)
            else:
                assert False, "unreachable"
        value = self.get_capture().strip()
        if value == "":
            value = "\n"
        else:
            value += " "
        return ast.EscapedFoldedLine(self.finish_capture(), value)

    def lex_name(self) -> Union[ast.Null, ast.Boolean, ast.Float, ast.Name]:
        c = self.save_and_next()
        while self.is_letter(c) or c in "0123456789":
            c = self.save_and_next()
        value = self.get_capture()
        if value == "null":
            return ast.Null(self.finish_capture(), value=None)
        elif value == "true":
            return ast.Boolean(self.finish_capture(), value=True)
        elif value == "false":
            return ast.Boolean(self.finish_capture(), value=False)
        elif value == "inf":
            return ast.Float(self.finish_capture(), value=inf)
        elif value == "nan":
            return ast.Float(self.finish_capture(), value=nan)
        else:
            return ast.Name(self.finish_capture(), value=value)

    def lex_punc(self, tok_type: Type[TokenT]) -> TokenT:
        self.next()
        return tok_type(self.finish_capture())

    def consume_escape(self) -> None:  # noqa: C901
        c = self.next()
        if c in "\\":
            self.next()
            self.save("\\")
        elif c in '"':
            self.next()
            self.save('"')
        elif c in "/":
            self.next()
            self.save("/")
        elif c in "b":
            self.next()
            self.save("\b")
        elif c in "n":
            self.next()
            self.save("\n")
        elif c in "r":
            self.next()
            self.save("\r")
        elif c in "t":
            self.next()
            self.save("\t")
        elif c == "x":
            self.consume_hex(2)
        elif c == "u":
            self.consume_hex(4)
        elif c == "U":
            self.consume_hex(8)
        else:
            raise ParseError(...)

    def consume_hex(self, n: int) -> None:
        local_capture: List[str] = []
        for _ in range(n):
            c = self.next()
            if self.is_hex(c):
                local_capture.append(c)
            else:
                raise ParseError(...)
        self.save(chr(int("".join(local_capture), 16)))

    def next(self) -> str:
        if self.curr == "\n":
            self.lineno += 1
            self.charno = 0
        else:
            self.charno += 1
        if self.lookahead is None:
            self.curr = self.stream.read(1)
        else:
            self.curr, self.lookahead = self.lookahead, None
        return self.curr

    def peek(self) -> str:
        if self.lookahead is None:
            self.lookahead = self.stream.read(1)
        return self.lookahead

    def save(self, c: str) -> None:
        self.capture.append(c)

    def save_and_next(self) -> str:
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

    @staticmethod
    def is_digit(c: str) -> bool:
        return c in "0123456789"

    @staticmethod
    def is_hex(c: str) -> bool:
        return c in "0123456789abcdefABCDEF"

    @staticmethod
    def is_letter(c: str) -> bool:
        return c in "_" or "a" <= c <= "z" or "A" <= c <= "Z" or c >= "\xA0"

    @staticmethod
    def is_character(c: str) -> bool:
        return "\x20" <= c < "\x7F" or c >= "\xA0"

    @staticmethod
    def is_control_code(c: str) -> bool:
        return "\x00" <= c < "\x20" or "\x7F" <= c < "\xA0"
