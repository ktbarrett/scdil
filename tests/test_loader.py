from textwrap import dedent
from typing import cast

from scdil import load
from scdil.frozendict import FrozenDict
from scdil.types import SCDILValue


def test_1() -> None:
    assert (
        load(
            r"""
        a: [1, 2, {"a": 1}]
        b: - - 1
             - false
             - 0.1
        "c": d: null
        """
        )
        == cast(
            SCDILValue,
            {"a": [1, 2, {"a": 1}], "b": [[1, False, 0.1]], "c": {"d": None}},
        )
    )


def test_2() -> None:
    assert (
        load(
            r"""
        {{}: null, [1, 2, 3]: null}
        """
        )
        == cast(SCDILValue, {FrozenDict(): None, (1, 2, 3): None})
    )


def test_3() -> None:
    assert (
        load(
            """
        |for i in range(10):
        |    if i % 2 == 0:
        |        print(i)
        """
        )
        == dedent(
            """\
        for i in range(10):
            if i % 2 == 0:
                print(i)
        """
        )
    )


def test_4() -> None:
    assert (
        load(
            """
        >This is a long
        >sentence, split
        >over many lines.
        >
        >And here is another
        >long sentence.
        """
        )
        == "This is a long sentence, split over many lines.\nAnd here is another long sentence."
    )
