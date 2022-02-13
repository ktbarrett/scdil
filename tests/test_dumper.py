from textwrap import dedent

from scdil import dumps


def test_dump_1() -> None:
    assert dumps({"a": 1, "b": {"c": 1}}) == dedent(
        """\
        a: 1
        b:
          c: 1
        """
    )
