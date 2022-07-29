import sys
from abc import abstractmethod
from typing import (
    Any,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    Mapping,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    ValuesView,
    overload,
)

_K = TypeVar("_K")
_V = TypeVar("_V")
_V_co = TypeVar("_V_co", covariant=True)


class _SupportsKeysAndGetItem(Protocol[_K, _V_co]):
    """ """

    @abstractmethod
    def keys(self) -> Iterable[_K]:
        ...

    @abstractmethod
    def __getitem__(self, item: _K) -> _V_co:
        ...


class FrozenDict(Mapping[_K, _V_co]):
    """ """

    @overload
    def __init__(self) -> None:
        ...

    @overload
    def __init__(self: "FrozenDict[str, _V_co]", **kwargs: _V_co) -> None:
        ...

    @overload
    def __init__(self, __map: _SupportsKeysAndGetItem[_K, _V_co]) -> None:
        ...

    @overload
    def __init__(
        self: "FrozenDict[Union[str, _K], _V_co]",
        __map: _SupportsKeysAndGetItem[_K, _V_co],
        **kwargs: _V_co,
    ) -> None:
        ...

    @overload
    def __init__(self, __iterable: Iterable[Tuple[_K, _V_co]]) -> None:
        ...

    @overload
    def __init__(
        self: "FrozenDict[Union[str, _K], _V_co]",
        __iterable: Iterable[Tuple[_K, _V_co]],
        **kwargs: _V_co,
    ) -> None:
        ...

    @overload
    def __init__(self: "FrozenDict[str, str]", __iterable: Iterable[List[str]]) -> None:
        ...

    def __init__(self, *args, **kwargs):  # type: ignore
        self._dict: Dict[_K, _V_co] = dict(*args, **kwargs)

    @classmethod
    def fromkeys(cls, __iterable: Iterable[_K], __value: _V) -> "FrozenDict[_K, _V]":
        return FrozenDict(dict.fromkeys(__iterable, __value))

    def __len__(self) -> int:
        return len(self._dict)

    def __getitem__(self, __item: _K) -> _V_co:
        return self._dict[__item]

    def __iter__(self) -> Iterator[_K]:
        return iter(self._dict)

    def __reversed__(self) -> Iterator[_K]:
        return reversed(self._dict)

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self._dict!r})"

    def __eq__(self, __other: object) -> bool:
        if isinstance(__other, dict):
            return self._dict == __other
        elif not isinstance(__other, type(self)):
            return NotImplemented
        else:
            return self._dict == __other._dict

    def __hash__(self) -> int:
        return sum(hash(item) for item in self.items())

    def copy(self) -> "FrozenDict[_K, _V_co]":
        return FrozenDict(self._dict.items())

    def keys(self) -> KeysView[_K]:
        return self._dict.keys()

    def values(self) -> ValuesView[_V_co]:
        return self._dict.values()

    def items(self) -> ItemsView[_K, _V_co]:
        return self._dict.items()

    if sys.version_info >= (3, 9):

        # dict supports '|' with disjoint types;
        # but mypy has a really hard time handling this correctly, so I don't bother
        #
        # def __or__(self, __other: Mapping[K2, V2]) -> "FrozenDict[_K | K2, _V_co | V2]":
        def __or__(self, __other: Mapping[_K, _V_co]) -> "FrozenDict[_K, _V_co]":
            if not isinstance(__other, Mapping):
                return NotImplemented
            res = FrozenDict(self)
            res |= __other
            return res

        def __ror__(self, __other: Mapping[_K, _V_co]) -> "FrozenDict[_K, _V_co]":
            if not isinstance(__other, Mapping):
                return NotImplemented
            res = FrozenDict(__other)
            res |= self
            return res

        def __ior__(self, __other: Mapping[_K, _V_co]) -> "FrozenDict[_K, _V_co]":
            self._dict |= __other
            return self

    def __class_getitem__(
        cls: Type["FrozenDict[_K, _V_co]"], __item: Any
    ) -> Type["FrozenDict[_K, _V_co]"]:
        return cls
