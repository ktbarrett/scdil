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
    return scdil_eval(ast, False)


@singledispatch
def scdil_eval(node: ast.Node, immutable: bool) -> Value:
    raise NotImplementedError  # pragma: no cover


@scdil_eval.register
def _(node: ast.Integer, immutable: bool) -> int:
    return node.value


@scdil_eval.register
def _(node: ast.Float, immutable: bool) -> float:
    return node.value


@scdil_eval.register
def _(node: ast.String, immutable: bool) -> str:
    return node.value


@scdil_eval.register
def _(node: ast.Null, immutable: bool) -> None:
    return None


@scdil_eval.register
def _(node: ast.Boolean, immutable: bool) -> bool:
    return node.value


@scdil_eval.register
def _(node: ast.Sequence, immutable: bool) -> Sequence:
    res = [scdil_eval(elem.value, immutable=immutable) for elem in node.elements]
    if immutable:
        return tuple(res)
    else:
        return res


@scdil_eval.register
def _(node: ast.Mapping, immutable: bool) -> Mapping:
    res: Dict[Value, Value] = {}
    for elem in node.elements:
        key: Value = scdil_eval(elem.key, immutable=True)
        value = scdil_eval(elem.value, immutable=immutable)
        res[key] = value
    if immutable:
        return FrozenDict(res)
    else:
        return res


@scdil_eval.register
def _(node: ast.BlockSequence, immutable: bool) -> Sequence:
    res = [scdil_eval(elem.value, immutable=immutable) for elem in node.elements]
    if immutable:
        return tuple(res)
    else:
        return res


@scdil_eval.register
def _(node: ast.BlockMapping, immutable: bool) -> Mapping:
    res: Dict[Value, Value] = {}
    for elem in node.elements:
        key = elem.key.value
        value = scdil_eval(elem.value, immutable=immutable)
        res[key] = value
    if immutable:
        return FrozenDict(res)
    else:
        return res


@scdil_eval.register
def _(node: ast.LiteralLines, immutable: bool) -> str:
    return "\n".join(line.value for line in node.lines)


@scdil_eval.register
def _(node: ast.FoldedLines, immutable: bool) -> str:
    return folded_lines(node.lines)


@scdil_eval.register
def _(node: ast.EscapedLiteralLines, immutable: bool) -> str:
    return "\n".join(line.value for line in node.lines)


@scdil_eval.register
def _(node: ast.EscapedFoldedLines, immutable: bool) -> str:
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
