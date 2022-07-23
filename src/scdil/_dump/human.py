from typing import TextIO, cast

import scdil._dump.machine as machine_dumper
from scdil.types import SCDILMapping, SCDILSequence, SCDILValue


def dump(value: SCDILValue, *, stream: TextIO) -> None:  # noqa: C901
    if value is None:
        machine_dumper.dump_null(stream=stream)
    elif isinstance(value, bool):
        machine_dumper.dump_bool(value, stream=stream)
    elif isinstance(value, int):
        machine_dumper.dump_int(value, stream=stream)
    elif isinstance(value, float):
        machine_dumper.dump_float(value, stream=stream)
    elif isinstance(value, str):
        if "\n" in value:
            dump_block_string(value, stream=stream, depth=0)
        else:
            machine_dumper.dump_str(value, stream=stream)
    elif isinstance(value, SCDILSequence):
        if len(value) == 0:
            stream.write("[]")
        else:
            dump_block_sequence(value, stream=stream, depth=0)
    elif isinstance(value, SCDILMapping):
        if len(value) == 0:
            stream.write("{}")
        elif all(isinstance(key, str) for key in value.keys()):
            dump_block_mapping(value, stream=stream, depth=0)
        else:
            dump_literal_mapping(value, stream=stream, depth=0)
    else:
        raise TypeError(f"Got unsupported type {type(value).__qualname__}")
    # always end the dump with a newline
    stream.write("\n")


def dump_literal(value: SCDILValue, *, stream: TextIO, depth: int) -> None:
    if value is None:
        machine_dumper.dump_null(stream=stream)
    elif isinstance(value, bool):
        machine_dumper.dump_bool(value, stream=stream)
    elif isinstance(value, int):
        machine_dumper.dump_int(value, stream=stream)
    elif isinstance(value, float):
        machine_dumper.dump_float(value, stream=stream)
    elif isinstance(value, str):
        machine_dumper.dump_str(value, stream=stream)
    elif isinstance(value, SCDILSequence):
        dump_literal_sequence(value, stream=stream, depth=depth)
    elif isinstance(value, SCDILMapping):
        dump_literal_mapping(value, stream=stream, depth=depth)
    else:
        raise TypeError(f"Got unsupported type {type(value).__qualname__}")


def dump_literal_sequence(value: SCDILSequence, *, stream: TextIO, depth: int) -> None:
    stream.write("[\n")
    line_start = "  " * (depth + 1)
    for elem in value:
        stream.write(line_start)
        dump_literal(elem, stream=stream, depth=(depth + 1))
        stream.write(",\n")
    stream.write("  " * depth)
    stream.write("]")


def dump_literal_mapping(value: SCDILMapping, *, stream: TextIO, depth: int) -> None:
    stream.write("{\n")
    line_start = "  " * (depth + 1)
    for key, val in value.items():
        stream.write(line_start)
        dump_literal(key, stream=stream, depth=(depth + 1))
        stream.write(": ")
        dump_literal(val, stream=stream, depth=(depth + 1))
        stream.write(",\n")
    stream.write("  " * depth)
    stream.write("}")


def dump_block_string(value: str, *, stream: TextIO, depth: int) -> None:
    next_line = "\n" + "  " * depth + "|"
    for line, last in machine_dumper.mark_last(value.splitlines()):
        machine_dumper.dump_line(line, stream=stream)
        if not last:
            stream.write(next_line)


def dump_block_sequence(value: SCDILSequence, *, stream: TextIO, depth: int) -> None:
    next_line = "\n" + "  " * depth
    for elem, last in machine_dumper.mark_last(value):
        stream.write("-")
        dump_block_sequence_elem(elem, stream=stream, depth=depth)
        if not last:
            stream.write(next_line)


def dump_block_sequence_elem(  # noqa: C901
    value: SCDILValue, *, stream: TextIO, depth: int
) -> None:
    if value is None:
        stream.write(" ")
        machine_dumper.dump_null(stream=stream)
    elif isinstance(value, bool):
        stream.write(" ")
        machine_dumper.dump_bool(value, stream=stream)
    elif isinstance(value, int):
        stream.write(" ")
        machine_dumper.dump_int(value, stream=stream)
    elif isinstance(value, float):
        stream.write(" ")
        machine_dumper.dump_float(value, stream=stream)
    elif isinstance(value, str):
        if "\n" in value:
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_string(value, stream=stream, depth=(depth + 1))
        else:
            stream.write(" ")
            machine_dumper.dump_str(value, stream=stream)
    elif isinstance(value, SCDILSequence):
        if len(value) == 0:
            stream.write(" []")
        else:
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_sequence(value, stream=stream, depth=(depth + 1))
    elif isinstance(value, SCDILMapping):
        if len(value) == 0:
            stream.write(" {}")
        elif all(isinstance(key, str) for key in value.keys()):
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_mapping(value, stream=stream, depth=(depth + 1))
        else:
            stream.write(" ")
            dump_literal_mapping(value, stream=stream, depth=(depth + 1))
    else:
        raise TypeError(f"Got unsupported type {type(value).__qualname__}")


def dump_block_mapping(value: SCDILMapping, *, stream: TextIO, depth: int) -> None:
    next_line = "\n" + "  " * depth
    for (key, val), last in machine_dumper.mark_last(value.items()):
        key = cast(str, key)
        dump_block_mapping_key(key, stream=stream)
        stream.write(":")
        dump_block_mapping_value(val, stream=stream, depth=depth)
        if not last:
            stream.write(next_line)


def dump_block_mapping_key(value: str, *, stream: TextIO) -> None:
    if value.isidentifier():
        # TODO: may be more or less forgiving than parser
        stream.write(value)
    else:
        # using single line quoted
        machine_dumper.dump_str(value, stream=stream)


def dump_block_mapping_value(  # noqa: C901
    value: SCDILValue, *, stream: TextIO, depth: int
) -> None:
    if value is None:
        stream.write(" ")
        machine_dumper.dump_null(stream=stream)
    elif isinstance(value, bool):
        stream.write(" ")
        machine_dumper.dump_bool(value, stream=stream)
    elif isinstance(value, int):
        stream.write(" ")
        machine_dumper.dump_int(value, stream=stream)
    elif isinstance(value, float):
        stream.write(" ")
        machine_dumper.dump_float(value, stream=stream)
    elif isinstance(value, str):
        if "\n" in value:
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_string(value, stream=stream, depth=(depth + 1))
        else:
            stream.write(" ")
            machine_dumper.dump_str(value, stream=stream)
    elif isinstance(value, SCDILSequence):
        if len(value) == 0:
            stream.write(" []")
        else:
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_sequence(value, stream=stream, depth=(depth + 1))
    elif isinstance(value, SCDILMapping):
        if len(value) == 0:
            stream.write(" {}")
        elif all(isinstance(key, str) for key in value.keys()):
            stream.write("\n")
            stream.write("  " * (depth + 1))
            dump_block_mapping(value, stream=stream, depth=(depth + 1))
        else:
            stream.write(" ")
            dump_literal_mapping(value, stream=stream, depth=(depth + 1))
    else:
        raise TypeError(f"Got unsupported type {type(value).__qualname__}")
