from dataclasses import dataclass
from typing import List, Optional, Union


@dataclass
class Node:
    ...


@dataclass
class SCDIL(Node):
    node: Union["Structure", "Value"]


@dataclass
class Structure(Node):
    ...


@dataclass
class Value(Node):
    ...


@dataclass
class Token(Node):
    lineno: int
    charno: int


@dataclass
class Null(Value, Token):
    ...


@dataclass
class Boolean(Value, Token):
    value: bool


@dataclass
class Number(Value, Token):
    value: float


@dataclass
class String(Value, Token):
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
class Name(Value, Token):
    value: str


@dataclass
class Dash(Token):
    ...


@dataclass
class Pipe(Token):
    ...


@dataclass
class Indent(Token):
    ...


@dataclass
class Nodent(Token):
    ...


@dataclass
class Dedent(Token):
    ...


@dataclass
class SequenceElement:
    value: Value
    comma: Optional[Comma]


@dataclass
class Sequence(Value):
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
class Mapping(Value):
    lcurly: LCurly
    elements: List[MappingElement]
    rcurly: RCurly


@dataclass
class Section:
    name: Name
    colon: Colon
    value: Value
    nodent: Optional[Nodent]


@dataclass
class Sections(Structure):
    indent: Indent
    elements: List[Section]
    dedent: Dedent


@dataclass
class Item:
    value: Value
    nodent: Optional[Nodent]


@dataclass
class Items(Structure):
    indent: Indent
    elements: List[Item]
    dedent: Dedent


@dataclass
class Paragraph(Structure):
    indent: Indent
    value: str
    dedent: Dedent
