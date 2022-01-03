import sys
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    ValuesView,
    overload,
)

from scdil.types import SupportsKeysAndGetItem

K = TypeVar("K")
V = TypeVar("V")
V_co = TypeVar("V_co", covariant=True)


class FrozenDict(Mapping[K, V_co]):
    """ """

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self, **kwargs: V_co) -> None:
        ...

    @overload
    def __init__(self, __map: SupportsKeysAndGetItem[K, V_co], **kwargs: V_co) -> None:
        ...

    @overload
    def __init__(self, __iterable: Iterable[Tuple[K, V_co]], **kwargs: V_co) -> None:
        ...

    @overload
    def __init__(self: "FrozenDict[str, str]", __iterable: Iterable[List[str]]) -> None:
        ...

    def __init__(self, *args, **kwargs):  # type: ignore
        self._dict: Dict[K, V_co] = dict(*args, **kwargs)

    @classmethod
    def fromkeys(cls, __iterable: Iterable[K], __value: V) -> "FrozenDict[K, V]":
        return FrozenDict(dict.fromkeys(__iterable, __value))

    def __len__(self) -> int:
        return len(self._dict)

    def __getitem__(self, __item: K) -> V_co:
        return self._dict[__item]

    def __iter__(self) -> Iterator[K]:
        return iter(self._dict)

    def __reversed__(self) -> Iterator[K]:
        return reversed(self._dict)

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self._dict!r})"

    def __eq__(self, __other: object) -> bool:
        if not isinstance(__other, type(self)):
            return NotImplemented
        return self._dict == __other._dict

    def __hash__(self) -> int:
        return sum(hash(item) for item in self.items())

    def copy(self) -> "FrozenDict[K, V_co]":
        return FrozenDict(self._dict.items())

    def keys(self) -> KeysView[K]:
        return self._dict.keys()

    def values(self) -> ValuesView[V_co]:
        return self._dict.values()

    def items(self) -> ItemsView[K, V_co]:
        return self._dict.items()

    if sys.version_info >= (3, 9):

        # dict supports '|' with disjoint types;
        # but mypy has a really hard time handling this correctly, so I don't bother
        #
        # def __or__(self, __other: Mapping[K2, V2]) -> "FrozenDict[K | K2, V_co | V2]":
        def __or__(self, __other: Mapping[K, V_co]) -> "FrozenDict[K, V_co]":
            if not isinstance(__other, Mapping):
                return NotImplemented
            res = self.copy()
            res |= __other
            return res

        def __ror__(self, __other: Mapping[K, V_co]) -> "FrozenDict[K, V_co]":
            if not isinstance(__other, Mapping):
                return NotImplemented
            res = self.copy()
            res |= __other
            return res

        def __ior__(self, __other: Mapping[K, V_co]) -> "FrozenDict[K, V_co]":
            self._dict |= __other
            return self

    def __class_getitem__(
        cls: Type["FrozenDict[K, V_co]"], __item: Any
    ) -> Type["FrozenDict[K, V_co]"]:
        return cls
