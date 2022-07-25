import math

import scdil
from scdil.types import SCDILValue


def dumps(value: SCDILValue) -> str:
    return scdil.dumps(value, for_humans=False)


def test_machine_dump_simple() -> None:
    assert dumps(None) == "null"
    assert dumps(True) == "true"
    assert dumps(False) == "false"
    assert dumps(-math.inf) == "-inf"
    assert dumps(math.inf) == "inf"
    assert dumps(math.nan) == "nan"
    assert dumps(-10) == "-10"
    assert dumps(1e8) == "100000000.0"
    assert dumps(math.pi).startswith("3.141592")
    assert (
        dumps("ab℞⽢⯫Ⳝ\x00\u007e\U00010111\n\r\t\\\"'")
        == '"ab℞⽢⯫Ⳝ\\x00~𐄑\\n\\r\\t\\\\\\"\'"'
    )
