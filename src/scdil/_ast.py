from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Position:
    lineno: int
    charno: int


@dataclass
class Token:
    position: Position


@dataclass
class Null(Token):
    value: None


@dataclass
class Boolean(Token):
    value: bool


@dataclass
class Integer(Token):
    value: int


@dataclass
class Float(Token):
    value: float


@dataclass
class String(Token):
    value: str


@dataclass
class Name(Token):
    value: str


@dataclass
class LiteralLine(Token):
    value: str


@dataclass
class FoldedLine(Token):
    value: str


@dataclass
class EscapedLiteralLine(Token):
    value: str


@dataclass
class EscapedFoldedLine(Token):
    value: str


@dataclass
class LBracket(Token):
    ...


@dataclass
class RBracket(Token):
    ...


@dataclass
class LCurly(Token):
    ...


@dataclass
class RCurly(Token):
    ...


@dataclass
class Comma(Token):
    ...


@dataclass
class Colon(Token):
    ...


@dataclass
class Dash(Token):
    ...


Node = Union["Value", "Block"]
Value = Union["Composite", "Scalar"]
Composite = Union["Sequence", "Mapping"]


@dataclass
class Scalar:
    value: Union[Null, Boolean, Integer, Float, String]

    @property
    def N(self) -> int:
        return self.value.position.charno


@dataclass
class SequenceElement:
    value: Value
    comma: Optional[Comma]


@dataclass
class Sequence:
    lbracket: LBracket
    elements: List[SequenceElement]
    rbracket: RBracket

    @property
    def N(self) -> int:
        return self.lbracket.position.charno


@dataclass
class MappingElement:
    key: Value
    colon: Colon
    value: Value
    comma: Optional[Comma]


@dataclass
class Mapping:
    lcurly: LCurly
    elements: List[MappingElement]
    rcurly: RCurly

    @property
    def N(self) -> int:
        return self.lcurly.position.charno


Block = Union["BlockMapping", "BlockSequence", "BlockString"]


@dataclass
class BlockSequenceElement:
    dash: Dash
    value: Node

    @property
    def N(self) -> int:
        return self.dash.position.charno


@dataclass
class BlockSequence:
    elements: List[BlockSequenceElement]

    @property
    def N(self) -> int:
        return self.elements[0].N


@dataclass
class BlockMappingElement:
    name: Union[Name, String]
    colon: Colon
    value: Node

    @property
    def N(self) -> int:
        return self.name.position.charno


@dataclass
class BlockMapping:
    elements: List[BlockMappingElement]

    @property
    def N(self) -> int:
        return self.elements[0].N


BlockString = Union[
    "LiteralLines", "FoldedLines", "EscapedLiteralLines", "EscapedFoldedLines"
]


@dataclass
class LiteralLines:
    lines: List[LiteralLine]

    @property
    def N(self) -> int:
        return self.lines[0].position.charno


@dataclass
class FoldedLines:
    lines: List[FoldedLine]

    @property
    def N(self) -> int:
        return self.lines[0].position.charno


@dataclass
class EscapedLiteralLines:
    lines: List[EscapedLiteralLine]

    @property
    def N(self) -> int:
        return self.lines[0].position.charno


@dataclass
class EscapedFoldedLines:
    lines: List[EscapedFoldedLine]

    @property
    def N(self) -> int:
        return self.lines[0].position.charno
