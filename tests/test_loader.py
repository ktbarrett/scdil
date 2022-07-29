from textwrap import dedent

from scdil import load
from scdil.frozendict import FrozenDict


def test_1() -> None:
    assert (
        load(
            dedent(
                """\
                a: [1, 2, {"a": 1}]
                b: - - 1
                     - false
                     - 0.1
                "c": d: null
                """
            )
        )
        == {"a": [1, 2, {"a": 1}], "b": [[1, False, 0.1]], "c": {"d": None}}
    )


def test_2() -> None:
    assert (
        load(
            dedent(
                """\
                {{}: null, [1, 2, 3]: null}
                """
            )
        )
        == {FrozenDict(): None, (1, 2, 3): None}
    )


def test_block_string() -> None:
    assert (
        load(
            dedent(
                """\
                |for i in range(10):
                |    if i % 2 == 0:
                |        print(i)
                |
                """
            )
        )
        == dedent(
            """\
            for i in range(10):
                if i % 2 == 0:
                    print(i)
        """
        )
    )
    assert (
        load(
            dedent(
                """\
                |abc
                |
                |def
                """
            )
        )
        == "abc\n\ndef"
    )


def test_block_folded_string() -> None:
    assert (
        load(
            """\
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
    assert (
        load(
            dedent(
                """\
                >123
                >
                >
                >       jeb
                >
                """
            )
        )
        == "123\n\njeb\n"
    )


def test_escaped_block_string() -> None:
    assert (
        load(
            dedent(
                """\
                \\|Control codes are \\x00 through \\x1F
                \\|and \\x7F through \\x9F.
                """
            )
        )
        == "Control codes are \x00 through \x1F\nand \x7F through \x9F."
    )


def test_escaped_block_folded_string() -> None:
    assert (
        load(
            dedent(
                """\
                \\>Control codes are \\x00 through \\x1F
                \\>and \\x7F through \\x9F.
                \\>
                """
            )
        )
        == "Control codes are \x00 through \x1F and \x7F through \x9F.\n"
    )
