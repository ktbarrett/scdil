import math
import random

import pytest

import scdil

identifiers = (
    tuple(chr(c) for c in range(ord("a"), ord("z") + 1))
    + tuple(chr(c) for c in range(ord("A"), ord("Z") + 1))
    + ("_",)
)


def generate_random_data(  # noqa: C901
    level: int = 0, immutable: bool = False
) -> scdil.Value:
    # ensure after 10 deep we only return terminals
    if level == 10:
        max_typ = 4
    else:
        max_typ = 7
    # choose type equally
    typ = random.randint(0, max_typ)
    if typ == 0:
        return None
    if typ == 1:
        return bool(random.randint(0, 1))
    elif typ == 2:
        # random signed 64 bit value
        return random.getrandbits(64) - 2**63
    elif typ == 3:
        # 2% chance each of nan, +inf, -inf, or 0.0
        sel = random.randint(0, 49)
        # nan != nan, so we just skip it
        # if sel == 0:
        #     return math.nan
        if sel == 1:
            return -math.inf
        elif sel == 2:
            return math.inf
        elif sel == 3:
            return 0.0
        else:
            # otherwise a random value either large 20% or small 80%
            if random.random() < 0.2:
                sigma = 2**100
            else:
                sigma = 100
            return random.gauss(0, sigma)
    elif typ == 4:
        return "".join(
            chr(random.randint(0, 0x1000)) for _ in range(random.randint(0, 100))
        )
    elif typ == 5:
        # mapping
        d = {}
        for _ in range(random.randint(0, 10)):
            key = generate_random_data(level=level + 1, immutable=True)
            value = generate_random_data(level=level + 1, immutable=immutable)
            d[key] = value
        if immutable:
            return scdil.FrozenDict(d)
        else:
            return d
    elif typ == 6:
        # sequence
        d = []
        for _ in range(random.randint(0, 10)):
            d.append(generate_random_data(level=level + 1, immutable=immutable))
        if immutable:
            return tuple(d)
        else:
            return d
    elif typ == 7:
        # specially a mapping with only string keys
        d = {}
        for _ in range(random.randint(0, 10)):
            # 20% of the time use names that must be quoted
            if random.random() < 0.2:
                key = "".join(
                    chr(random.randint(0, 0x10FFFF))
                    for _ in range(random.randint(0, 20))
                )
            else:
                key = "".join(random.choices(identifiers, k=random.randint(0, 20)))
            value = generate_random_data(level=level + 1, immutable=immutable)
            d[key] = value
        if immutable:
            return scdil.FrozenDict(d)
        else:
            return d


@pytest.mark.parametrize("seed", range(20))
def test_round_trip(seed: int) -> None:
    random.seed(seed)
    test_data = generate_random_data()
    test_dumped = scdil.dumps(test_data)
    test_loaded = scdil.load(test_dumped)
    assert test_loaded == test_data
