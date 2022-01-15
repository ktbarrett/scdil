from io import StringIO
from typing import TextIO, Union

from scdil.types import SCDILValue


def load(stream: Union[str, TextIO]) -> SCDILValue:
    """Creates a Python object from SCDIL text or file"""
    if isinstance(stream, str):
        stream = StringIO(stream)
    raise NotImplementedError
