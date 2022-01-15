from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Token:
    lineno: int
    charno: int


@dataclass
class Null(Token):
    value: None = None


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


SCDIL = Union["Value", "Block"]
Value = Union["Composite", "Scalar"]
Scalar = Union[Null, Boolean, Integer, Float, String]
Composite = Union["Sequence", "Mapping"]


@dataclass
class SequenceElement:
    value: Value
    comma: Optional[Comma]


@dataclass
class Sequence:
    lbracket: LBracket
    elements: List[SequenceElement]
    rbracket: RBracket


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


Block = Union["BlockMapping", "BlockSequence", "BlockString"]


@dataclass
class BlockSequenceElement:
    dash: Dash
    value: SCDIL


@dataclass
class BlockSequence:
    elements: List[BlockSequenceElement]


@dataclass
class BlockMappingElement:
    name: Union[Name, String]
    colon: Colon
    value: SCDIL


@dataclass
class BlockMapping:
    elements: List[BlockMappingElement]


BlockString = Union[
    "LiteralLines", "FoldedLines", "EscapedLiteralLines", "EscapedFoldedLines"
]


@dataclass
class LiteralLines:
    lines: List[LiteralLine]


@dataclass
class FoldedLines:
    lines: List[FoldedLine]


@dataclass
class EscapedLiteralLines:
    lines: List[EscapedLiteralLine]


@dataclass
class EscapedFoldedLines:
    lines: List[EscapedFoldedLine]
