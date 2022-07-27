import math
from textwrap import dedent

import pytest

from scdil import dumps


def test_human_dump() -> None:
    assert dumps(None) == "null\n"
    assert dumps(True) == "true\n"
    assert dumps(False) == "false\n"
    assert dumps(-math.inf) == "-inf\n"
    assert dumps(math.inf) == "inf\n"
    assert dumps(math.nan) == "nan\n"
    assert dumps(-10) == "-10\n"
    assert dumps(1e8) == "100000000.0\n"
    assert dumps(math.pi).startswith("3.141592")
    assert dumps("") == '""\n'


def test_singleline_string() -> None:
    assert dumps("abcd10-*#;asd'g/,.masdliu") == '"abcd10-*#;asd\'g/,.masdliu"\n'


def test_multiline_string() -> None:
    assert (
        dumps(
            dedent(
                """\
                lorem ipsum dolar
                foo bar baz
                """
            )
        )
        == dedent(
            """\
            |lorem ipsum dolar
            |foo bar baz
            |
            """
        )
    )


def test_escaped_singleline_string() -> None:
    assert dumps("\r\t\x00\xbe\xef") == '"\\r\\t\\x00\xbe\xef"\n'


def test_escaped_multiline_string() -> None:
    assert dumps("ab℞⽢⯫Ⳝ\x00\u007e\U00010111\n\r\t\\\"'") == dedent(
        """\
        \\|ab℞⽢⯫Ⳝ\\x00~𐄑
        \\|\\r\\t\\\\"'
        """
    )


def test_empty_string() -> None:
    assert dumps("") == '""\n'
    assert dumps("\n") == '"\\n"\n'


def test_empty_sequence() -> None:
    assert dumps([]) == "[]\n"


def test_empty_mapping() -> None:
    assert dumps({}) == "{}\n"


def test_simple_block_sequence() -> None:
    assert dumps([1, None, 3e8, False, "bottom text"]) == dedent(
        """\
        - 1
        - null
        - 300000000.0
        - false
        - "bottom text"
        """
    )


def test_simple_block_mapping() -> None:
    assert dumps({"a": 1, "b": None, "c": False, "d": -0.7}) == dedent(
        """\
        a: 1
        b: null
        c: false
        d: -0.7
        """
    )


def test_unsupported_type() -> None:
    with pytest.raises(TypeError):
        assert dumps(object())
    with pytest.raises(TypeError):
        assert dumps(set())


def test_sequence_element_is_sequence() -> None:
    assert dumps([[1, None, 0.008], False, []]) == dedent(
        """\
        -
          - 1
          - null
          - 0.008
        - false
        - []
        """
    )


def test_sequence_element_is_mapping() -> None:
    assert dumps([{"a": 1}, 123, {"b": 2}, None, {}]) == dedent(
        """\
        -
          a: 1
        - 123
        -
          b: 2
        - null
        - {}
        """
    )


def test_sequence_element_is_string() -> None:
    assert dumps([""]) == '- ""\n'
    assert dumps(["\n"]) == '- "\\n"\n'
    assert dumps(["sample!!!"]) == '- "sample!!!"\n'
    assert dumps(["abc\ndef\nghi"]) == dedent(
        """\
        -
          |abc
          |def
          |ghi
        """
    )
    assert dumps(["\x00\n\U00010111\n"]) == dedent(
        """\
        -
          \\|\\x00
          \\|\U00010111
          \\|
        """
    )


def test_sequence_element_is_unsupported() -> None:
    with pytest.raises(TypeError):
        dumps([object()])


def test_mapping_value_is_sequence() -> None:
    assert dumps({"a": [1, None, "dog"], "b": []}) == dedent(
        """\
        a:
          - 1
          - null
          - "dog"
        b: []
        """
    )


def test_mapping_value_is_mapping() -> None:
    assert dumps({"a": 1, "b": {"c": 1}, "d": {}}) == dedent(
        """\
        a: 1
        b:
          c: 1
        d: {}
        """
    )


def test_mapping_value_is_string() -> None:
    assert dumps({"a": ""}) == 'a: ""\n'
    assert dumps({"a": "\n"}) == 'a: "\\n"\n'
    assert dumps({"a": "wow"}) == 'a: "wow"\n'
    assert dumps({"a": "wew\nlad"}) == dedent(
        """\
        a:
          |wew
          |lad
        """
    )
    assert dumps({"a": "\x10\x01\n\r\t"}) == dedent(
        """\
        a:
          \\|\\x10\\x01
          \\|\\r\\t
        """
    )


def test_mapping_value_is_literal_mapping() -> None:
    assert dumps({"a": {None: 1}}) == dedent(
        """\
        a: {
            null: 1
          }
        """
    )


def test_mapping_name_needs_quotes() -> None:
    assert dumps({"wew lad": 1}) == dedent(
        """\
        "wew lad": 1
        """
    )


def test_mapping_value_is_unsupported() -> None:
    with pytest.raises(TypeError):
        dumps({"a": object()})


def test_literal_mapping() -> None:
    assert dumps({"a": 1, None: [False, {}, -789, {"6": 6}]}) == dedent(
        """\
        {
          "a": 1,
          null: [
            false,
            {},
            -789,
            {
              "6": 6
            }
          ]
        }
        """
    )


def test_sequence_element_is_literal_mapping() -> None:
    assert dumps([{"a": 1, None: [True, {}, -789.0, {"": 6}, []]}]) == dedent(
        """\
        - {
            "a": 1,
            null: [
              true,
              {},
              -789.0,
              {
                "": 6
              },
              []
            ]
          }
        """
    )


def test_unsuported_type_in_literal() -> None:
    with pytest.raises(TypeError):
        dumps({None: object()})
