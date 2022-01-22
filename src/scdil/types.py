from abc import abstractmethod
from typing import (
    ItemsView,
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

# Recursive type aliases are not currently supported python/mypy#731
#
# SCDILValue = Union[None, bool, int, float, str, "Sequence[SCDILValue]", "Mapping[SCDILValue, SCDILValue]"]
SCDILValue = Union[None, bool, int, float, str, "SCDILSequence", "SCDILMapping"]


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

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        ...

    @abstractmethod
    def __getitem__(self, item: int) -> SCDILValue:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[SCDILValue]:
        ...

    @abstractmethod
    def index(self, item: object, start: int = ..., stop: int = ...) -> int:
        ...

    @abstractmethod
    def count(self, item: object) -> int:
        ...


@runtime_checkable
class SCDILMapping(Protocol):
    """ """

    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        ...

    @abstractmethod
    def __getitem__(self, item: SCDILValue) -> SCDILValue:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[SCDILValue]:
        ...

    @overload
    def get(self, item: object) -> Optional[SCDILValue]:
        ...

    @overload
    def get(self, item: object, default: T) -> Union[SCDILValue, T]:
        ...

    @abstractmethod
    def keys(self) -> KeysView[SCDILValue]:
        ...

    @abstractmethod
    def values(self) -> ValuesView[SCDILValue]:
        ...

    @abstractmethod
    def items(self) -> ItemsView[SCDILValue, SCDILValue]:
        ...
