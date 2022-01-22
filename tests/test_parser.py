from dataclasses import dataclass
from io import StringIO
from math import inf, nan
from textwrap import dedent
from typing import List, Optional

import pytest

import scdil._ast as ast
from scdil._parse import Lexer, ParseError, Parser


def tokenize(source: str) -> List[ast.Token]:
    return list(Lexer(StringIO(source)))


def single_token(source: str) -> ast.Token:
    toks = tokenize(source)
    assert len(toks) == 1
    return toks[0]


def test_lex_names() -> None:
    assert isinstance(single_token("null"), ast.Null)
    assert isinstance(tok := single_token("true"), ast.Boolean) and tok.value is True
    assert isinstance(tok := single_token("false"), ast.Boolean) and tok.value is False
    assert (
        isinstance(tok := single_token("_GeorgeCostanza94"), ast.Name)
        and tok.value == "_GeorgeCostanza94"
    )
    assert (
        isinstance(tok := single_token("♴ⱳ⫹ⷻ℞⽢⯫Ⳝⲝ➎⠶⁑⸛⧘⹘ⵦ⻵ℑ⠧‎⪿╎⍻⑊⯂⁼┿⼳ⱏ⊏⛙⯅☞⾦⥄"), ast.Name)
        and tok.value == "♴ⱳ⫹ⷻ℞⽢⯫Ⳝⲝ➎⠶⁑⸛⧘⹘ⵦ⻵ℑ⠧‎⪿╎⍻⑊⯂⁼┿⼳ⱏ⊏⛙⯅☞⾦⥄"
    )


def test_lex_named_numbers() -> None:
    assert isinstance(tok := single_token("inf"), ast.Float) and tok.value == inf
    assert isinstance(tok := single_token("nan"), ast.Float) and tok.value is nan
    assert isinstance(tok := single_token("+inf"), ast.Float) and tok.value == inf
    assert isinstance(tok := single_token("-inf"), ast.Float) and tok.value == -inf
    with pytest.raises(ParseError):
        single_token("-one")


def test_lex_integer() -> None:
    assert isinstance(tok := single_token("0"), ast.Integer) and tok.value == 0
    assert isinstance(tok := single_token("-1"), ast.Integer) and tok.value == -1
    assert isinstance(tok := single_token("+01"), ast.Integer) and tok.value == 1
    assert isinstance(tok := single_token("0123"), ast.Integer) and tok.value == 123
    assert (
        isinstance(tok := single_token("623896"), ast.Integer) and tok.value == 623896
    )
    assert isinstance(tok := single_token("0x123"), ast.Integer) and tok.value == 0x123
    assert (
        isinstance(tok := single_token("0o00142"), ast.Integer) and tok.value == 0o00142
    )
    assert (
        isinstance(tok := single_token("0B110101"), ast.Integer)
        and tok.value == 0b110101
    )
    with pytest.raises(ParseError):
        single_token("+-")
    with pytest.raises(ParseError):
        single_token("0XJ6")
    with pytest.raises(ParseError):
        single_token("0oDEAD")
    with pytest.raises(ParseError):
        single_token("0b2")


def test_lex_float() -> None:
    assert isinstance(tok := single_token("0."), ast.Float) and tok.value == 0.0
    assert (
        isinstance(tok := single_token("0.789123"), ast.Float) and tok.value == 0.789123
    )
    assert isinstance(tok := single_token("+0e0"), ast.Float) and tok.value == 0.0
    assert isinstance(tok := single_token("0e-1"), ast.Float) and tok.value == 0.0
    assert isinstance(tok := single_token("0.e0"), ast.Float) and tok.value == 0.0
    assert (
        isinstance(tok := single_token("-0123.123e+123"), ast.Float)
        and tok.value == -0123.123e123
    )
    with pytest.raises(ParseError):
        single_token("0eb")


def test_lex_string() -> None:
    assert isinstance(tok := single_token('"abc"'), ast.String) and tok.value == "abc"
    assert (
        isinstance(tok := single_token('"\\\\\\"\\/\\b\\f\\n\\r\\t"'), ast.String)
        and tok.value == '\\"/\b\f\n\r\t'
    )
    assert (
        isinstance(tok := single_token('"\\x7F\\u0Fa9\\U0001F6a6"'), ast.String)
        and tok.value == "\x7F\u0Fa9\U0001F6a6"
    )
    with pytest.raises(ParseError):
        single_token('"whoops')
    with pytest.raises(ParseError):
        single_token('"whoops\n"')
    with pytest.raises(ParseError):
        single_token('"whoops\t"')
    with pytest.raises(ParseError):
        single_token('"\\j"')
    with pytest.raises(ParseError):
        single_token('"\\xM0')


def test_lex_line() -> None:
    assert (
        isinstance(tok := single_token("|wow \\x76\n"), ast.LiteralLine)
        and tok.value == "wow \\x76"
    )
    assert (
        isinstance(tok := single_token(">   wow \\x76    \n"), ast.FoldedLine)
        and tok.value == "   wow \\x76    "
    )
    assert (
        isinstance(tok := single_token(">   \n"), ast.FoldedLine) and tok.value == "   "
    )
    assert (
        isinstance(tok := single_token("\\|wow \\x76"), ast.EscapedLiteralLine)
        and tok.value == "wow \x76"
    )
    assert (
        isinstance(tok := single_token("\\>   wow \\x76    \n"), ast.EscapedFoldedLine)
        and tok.value == "   wow \x76    "
    )
    assert (
        isinstance(tok := single_token("\\>   \n"), ast.EscapedFoldedLine)
        and tok.value == "   "
    )
    with pytest.raises(ParseError):
        single_token("|\t\n")
    with pytest.raises(ParseError):
        single_token(">\t\n")
    with pytest.raises(ParseError):
        single_token("\\|\t\n")
    with pytest.raises(ParseError):
        single_token("\\>\t\n")


def test_lex_punc() -> None:
    assert isinstance(single_token("["), ast.LBracket)
    assert isinstance(single_token("]"), ast.RBracket)
    assert isinstance(single_token("{"), ast.LCurly)
    assert isinstance(single_token("}"), ast.RCurly)
    assert isinstance(single_token(":"), ast.Colon)
    assert isinstance(single_token(","), ast.Comma)
    assert isinstance(single_token("- "), ast.Dash)


def test_lex_misc() -> None:
    assert isinstance(single_token(" \n   # skip this\n123 #value is 123"), ast.Integer)
    with pytest.raises(ParseError):
        single_token("\tinvalid")
    with pytest.raises(ParseError):
        single_token("$invalid")


@dataclass(eq=False)
class MockPosition(ast.Position):
    """Equates True to any Position"""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ast.Position)


any_pos = MockPosition(-1, -1)


def parse(source: str) -> Optional[ast.Node]:
    return Parser(StringIO(source)).parse()


def test_parse_scalars() -> None:
    assert parse("-0.123") == ast.Scalar(ast.Float(any_pos, -0.123))
    assert parse("true  # wew") == ast.Scalar(ast.Boolean(any_pos, True))
    assert parse("  null") == ast.Scalar(ast.Null(any_pos, None))
    assert parse('"123"') == ast.Scalar(ast.String(any_pos, "123"))
    assert parse("#comment\n  +0 ") == ast.Scalar(ast.Integer(any_pos, 0))


def test_parse_sequence() -> None:
    assert parse('[123, "123",]') == ast.Sequence(
        ast.LBracket(any_pos),
        [
            ast.SequenceElement(
                ast.Scalar(ast.Integer(any_pos, 123)), ast.Comma(any_pos)
            ),
            ast.SequenceElement(
                ast.Scalar(ast.String(any_pos, "123")), ast.Comma(any_pos)
            ),
        ],
        ast.RBracket(any_pos),
    )


def test_parse_mapping() -> None:
    assert parse('{"a":\n1,null:-123e-5\n  #comment\n}  # value') == ast.Mapping(
        ast.LCurly(any_pos),
        [
            ast.MappingElement(
                ast.Scalar(ast.String(any_pos, "a")),
                ast.Colon(any_pos),
                ast.Scalar(ast.Integer(any_pos, 1)),
                ast.Comma(any_pos),
            ),
            ast.MappingElement(
                ast.Scalar(ast.Null(any_pos, None)),
                ast.Colon(any_pos),
                ast.Scalar(ast.Float(any_pos, -123e-5)),
                None,
            ),
        ],
        ast.RCurly(any_pos),
    )


def test_parse_block_sequence() -> None:
    assert (
        parse(
            dedent(
                """
                - 1
                - "example"
                """
            )
        )
        == ast.BlockSequence(
            [
                ast.BlockSequenceElement(
                    ast.Dash(any_pos),
                    ast.Scalar(ast.Integer(any_pos, 1)),
                ),
                ast.BlockSequenceElement(
                    ast.Dash(any_pos),
                    ast.Scalar(ast.String(any_pos, "example")),
                ),
            ]
        )
    )


def test_parse_block_mapping() -> None:
    assert (
        parse(
            dedent(
                """
                a: 1
                "b": "example"
                """
            )
        )
        == ast.BlockMapping(
            [
                ast.BlockMappingElement(
                    ast.Name(any_pos, "a"),
                    ast.Colon(any_pos),
                    ast.Scalar(ast.Integer(any_pos, 1)),
                ),
                ast.BlockMappingElement(
                    ast.String(any_pos, "b"),
                    ast.Colon(any_pos),
                    ast.Scalar(ast.String(any_pos, "example")),
                ),
            ]
        )
    )


def test_parse_literal_lines() -> None:
    assert (
        parse(
            dedent(
                """
        |for i in range(10):
        |    if i % 2 == 0:
        |        print(i)
        """
            )
        )
        == ast.LiteralLines(
            [
                ast.LiteralLine(any_pos, "for i in range(10):"),
                ast.LiteralLine(any_pos, "    if i % 2 == 0:"),
                ast.LiteralLine(any_pos, "        print(i)"),
            ]
        )
    )


def test_parse_folded_lines() -> None:
    assert (
        parse(
            dedent(
                """
        >Česká zbrojovka
        >Застава oружје
        >Императорский Тульский оружейный завод
        """
            )
        )
        == ast.FoldedLines(
            [
                ast.FoldedLine(any_pos, "Česká zbrojovka"),
                ast.FoldedLine(any_pos, "Застава oружје"),
                ast.FoldedLine(any_pos, "Императорский Тульский оружейный завод"),
            ]
        )
    )


def test_parse_escaped_literal_lines() -> None:
    assert (
        parse(
            dedent(
                r"""
        \|Smile!
        \|\U0001F60A
        """
            )
        )
        == ast.EscapedLiteralLines(
            [
                ast.EscapedLiteralLine(any_pos, "Smile!"),
                ast.EscapedLiteralLine(any_pos, "😊"),
            ]
        )
    )


def test_parse_escaped_folded_lines() -> None:
    assert (
        parse(
            dedent(
                r"""
        \>a\x62c
        \>\u00312\U00000033
        """
            )
        )
        == ast.EscapedFoldedLines(
            [
                ast.EscapedFoldedLine(any_pos, "abc"),
                ast.EscapedFoldedLine(any_pos, "123"),
            ]
        )
    )
