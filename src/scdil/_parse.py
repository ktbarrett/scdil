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

    def peek_tok(self, i: int = 1) -> Optional[ast.Token]:
        ...

    def next_tok(self, i: int = 1) -> Optional[ast.Token]:
        ...

    def parse(self) -> Optional[ast.SCDIL]:
        if (parse := self.parse_scdil()) is not None:
            if self.curr_tok is None:
                return parse
            else:
                raise ParseError("Expected end of end of token stream")
        else:
            return None

    def parse_scdil(self) -> Optional[ast.SCDIL]:
        if (parse := self.parse_value()) is not None:
            return parse
        elif (parse2 := self.parse_block()) is not None:
            return parse2
        else:
            return None

    def parse_value(self) -> Optional[ast.Value]:
        if (parse := self.parse_scalar()) is not None:
            return parse
        elif (parse2 := self.parse_composite()) is not None:
            return parse2
        else:
            return None

    def parse_scalar(self) -> Optional[ast.Scalar]:
        if isinstance(self.peek_tok(), ast.Scalar):
            return self.next_tok()
        else:
            return None

    def parse_composite(self) -> Optional[ast.Composite]:
        if (parse := self.parse_sequence()) is not None:
            return parse
        elif (parse2 := self.parse_mapping()) is not None:
            return parse2
        else:
            return None

    def parse_sequence(self) -> Optional[ast.Sequence]:
        if not isinstance(lbracket := self.peek_tok(), ast.LBracket):
            return None
        else:
            self.next_tok()
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

    def parse_sequence_element(self) -> Optional[ast.SequenceElement]:
        if (value := self.parse_value()) is None:
            return None
        if isinstance(comma := self.peek_tok(), ast.Comma):
            self.next_tok()
        else:
            comma = None
        return ast.SequenceElement(
            value=value,
            comma=comma,
        )

    def parse_mapping(self) -> Optional[ast.Mapping]:
        if not isinstance(lcurly := self.peek_tok(), ast.LCurly):
            return None
        else:
            self.next_tok()
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

    def parse_mapping_element(self) -> Optional[ast.MappingElement]:
        if (key := self.parse_value()) is None:
            return None
        if not isinstance(colon := self.next_tok(), ast.Colon):
            raise ParseError(...)
        if (value := self.parse_value()) is None:
            raise ParseError(...)
        if isinstance(comma := self.peek_tok(), ast.Comma):
            self.next_tok()
        else:
            comma = None
        return ast.MappingElement(
            key=key,
            colon=colon,
            value=value,
            comma=comma,
        )

    def parse_block(self) -> Optional[ast.Block]:
        if (block1 := self.parse_block_sequence()) is not None:
            return block1
        elif (block2 := self.parse_block_mapping()) is not None:
            return block2
        elif (block3 := self.parse_block_string()) is not None:
            return block3
        else:
            return None

    def parse_block_sequence(self) -> Optional[ast.BlockSequence]:
        ...

    def parse_block_sequence_element(self) -> Optional[ast.BlockSequenceElement]:
        ...

    def parse_block_mapping(self) -> Optional[ast.BlockMapping]:
        ...

    def parse_block_mapping_element(self) -> Optional[ast.BlockMappingElement]:
        ...

    def parse_block_string(self) -> Optional[ast.BlockString]:
        if (block1 := self.parse_literal_lines()) is not None:
            return block1
        elif (block2 := self.parse_folded_lines()) is not None:
            return block2
        elif (block3 := self.parse_escaped_literal_lines()) is not None:
            return block3
        elif (block4 := self.parse_escaped_folded_lines()) is not None:
            return block4
        else:
            return None

    def parse_literal_lines(self) -> Optional[ast.LiteralLines]:
        ...

    def parse_folded_lines(self) -> Optional[ast.FoldedLines]:
        ...

    def parse_escaped_literal_lines(self) -> Optional[ast.EscapedLiteralLines]:
        ...

    def parse_escaped_folded_lines(self) -> Optional[ast.EscapedFoldedLines]:
        ...
