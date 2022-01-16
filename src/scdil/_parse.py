from typing import List, Optional, TextIO

import scdil._ast as ast


class ParseError(Exception):
    ...


class Parser:
    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._lineno = 0
        self._charno = 0
        self.curr_ch: str
        self._start_lineno = 0
        self._start_charno = 0
        self.curr_tok: Optional[ast.Token]

    @staticmethod
    def get_N(token: ast.Token) -> int:
        return token.charno

    @staticmethod
    def check_N(token: ast.Token, N: Optional[int]) -> bool:
        return N is not None and Parser.get_N(token) == N

    def parse(self) -> Optional[ast.Node]:
        if (parse := self.parse_node(None)) is not None:
            if self.curr_tok is None:
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
        ...

    def next_tok(self) -> Optional[ast.Token]:
        ...
