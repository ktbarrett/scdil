from typing import (
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    Optional,
    Protocol,
    TypeVar,
    Union,
    ValuesView,
    overload,
    runtime_checkable,
)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

# Recursive type aliases are not currently supported python/mypy#731
#
# SCDILValue = Union[None, bool, float, str, "Sequence[SCDILValue]", "Mapping[SCDILValue, SCDILValue]"]
SCDILValue = Union[None, bool, float, str, "SCDILSequence", "SCDILMapping"]


# Sequence and Mapping are not Protocols, so we can't just inherit
# Wouldn't matter anyway since tuple is not a Sequence structurally
# We have to define a Sequence without a __reversed__ to match it
#
# @runtime_checkable
# class SCDILSequence(Sequence[SCDILValue], Protocol):
#    ...


@runtime_checkable
class SCDILSequence(Protocol):
    """ """

    def __len__(self) -> int:
        ...

    def __contains__(self, item: object) -> bool:
        ...

    def __getitem__(self, item: int) -> SCDILValue:
        ...

    def __iter__(self) -> Iterator[SCDILValue]:
        ...

    def index(self, item: object, start: int = ..., stop: int = ...) -> int:
        ...

    def count(self, item: object) -> int:
        ...


@runtime_checkable
class SCDILMapping(Protocol):
    """ """

    def __len__(self) -> int:
        ...

    def __contains__(self, item: object) -> bool:
        ...

    def __getitem__(self, item: SCDILValue) -> SCDILValue:
        ...

    def __iter__(self) -> Iterator[SCDILValue]:
        ...

    @overload
    def get(self, item: object) -> Optional[SCDILValue]:
        ...

    @overload
    def get(self, item: object, default: T) -> Union[SCDILValue, T]:
        ...

    def keys(self) -> KeysView[SCDILValue]:
        ...

    def values(self) -> ValuesView[SCDILValue]:
        ...

    def items(self) -> ItemsView[SCDILValue, SCDILValue]:
        ...


class SupportsKeysAndGetItem(Protocol[T, T_co]):
    """ """

    def keys(self) -> Iterable[T]:
        ...

    def __getitem__(self, item: T) -> T_co:
        ...
