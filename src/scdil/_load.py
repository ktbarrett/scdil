from functools import singledispatch
from io import StringIO
from typing import Dict, List, TextIO, Union

import scdil._ast as ast
from scdil._frozendict import FrozenDict
from scdil._parse import Parser
from scdil._types import Mapping, Sequence, Value


def load(stream: Union[str, TextIO]) -> Value:
    """Creates a Python object from SCDIL text or file"""
    if isinstance(stream, str):
        stream = StringIO(stream)
    parser = Parser(stream)
    ast = parser.parse()
    return scdil_eval(ast)


@singledispatch
def scdil_eval(node: ast.Node) -> Value:
    raise NotImplementedError  # pragma: no cover


@scdil_eval.register
def _(node: ast.Integer) -> int:
    return node.value


@scdil_eval.register
def _(node: ast.Float) -> float:
    return node.value


@scdil_eval.register
def _(node: ast.String) -> str:
    return node.value


@scdil_eval.register
def _(node: ast.Null) -> None:
    return None


@scdil_eval.register
def _(node: ast.Boolean) -> bool:
    return node.value


@scdil_eval.register
def _(node: ast.Sequence) -> Sequence:
    return [scdil_eval(elem.value) for elem in node.elements]


@scdil_eval.register
def _(node: ast.Mapping) -> Mapping:
    res: Dict[Value, Value] = {}
    for elem in node.elements:
        key: Value = scdil_eval(elem.key)
        if isinstance(key, dict):
            key = FrozenDict(key)
        elif isinstance(key, list):
            key = tuple(key)
        value = scdil_eval(elem.value)
        res[key] = value
    return res


@scdil_eval.register
def _(node: ast.BlockSequence) -> Sequence:
    return [scdil_eval(elem.value) for elem in node.elements]


@scdil_eval.register
def _(node: ast.BlockMapping) -> Mapping:
    res: Dict[Value, Value] = {}
    for elem in node.elements:
        key = elem.key.value
        value = scdil_eval(elem.value)
        res[key] = value
    return res


@scdil_eval.register
def _(node: ast.LiteralLines) -> str:
    return "\n".join(line.value for line in node.lines)


@scdil_eval.register
def _(node: ast.FoldedLines) -> str:
    return folded_lines(node.lines)


@scdil_eval.register
def _(node: ast.EscapedLiteralLines) -> str:
    return "\n".join(line.value for line in node.lines)


@scdil_eval.register
def _(node: ast.EscapedFoldedLines) -> str:
    return folded_lines(node.lines)


def folded_lines(
    lines: Union[List[ast.FoldedLine], List[ast.EscapedFoldedLine]]
) -> str:
    s: List[str] = []
    prev_line_empty = True
    for line in lines:
        value = line.value.strip(" ")
        line_empty = value == ""
        if line_empty:
            s.append("\n")
        elif prev_line_empty:
            s.append(value)
        else:
            s.append(" ")
            s.append(value)
        prev_line_empty = line_empty
    return "".join(s)
