from io import StringIO
from math import inf, nan
from typing import List

import pytest

import scdil._ast as ast
from scdil._parse import Lexer, ParseError


def tokenize(source: str) -> List[ast.Token]:
    return list(Lexer(StringIO(source)))


def single_token(source: str) -> ast.Token:
    toks = tokenize(source)
    assert len(toks) == 1
    return toks[0]


def test_names() -> None:
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


def test_named_numbers() -> None:
    assert isinstance(tok := single_token("inf"), ast.Float) and tok.value == inf
    assert isinstance(tok := single_token("nan"), ast.Float) and tok.value is nan
    assert isinstance(tok := single_token("+inf"), ast.Float) and tok.value == inf
    assert isinstance(tok := single_token("-inf"), ast.Float) and tok.value == -inf
    with pytest.raises(ParseError):
        single_token("-one")


def test_integer() -> None:
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


def test_float() -> None:
    assert isinstance(tok := single_token("0."), ast.Float) and tok.value == 0.0
    assert (
        isinstance(tok := single_token("0.789123"), ast.Float) and tok.value == 0.789123
    )
    assert isinstance(tok := single_token("0e0"), ast.Float) and tok.value == 0.0
    assert isinstance(tok := single_token("0e-1"), ast.Float) and tok.value == 0.0
    assert isinstance(tok := single_token("0.e0"), ast.Float) and tok.value == 0.0
    assert (
        isinstance(tok := single_token("0123.123e+123"), ast.Float)
        and tok.value == 0123.123e123
    )
    with pytest.raises(ParseError):
        single_token("0eb")
