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
# SCDILSequence and SCDILMapping are a workaround
#
# SCDILValue = Union[None, bool, int, float, str, "Sequence[SCDILValue]", "Mapping[SCDILValue, SCDILValue]"]
SCDILValue = Union[None, bool, int, float, str, "SCDILSequence", "SCDILMapping"]


@runtime_checkable
class SCDILSequence(Protocol):
    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, item: int) -> SCDILValue:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, item: slice) -> "SCDILSequence":
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[SCDILValue]:
        ...

    # tuple does not have a public __reversed__ method, but implements reversed() in some special way.
    # We don't really need reversed() for this library to function, so we will leave this out for now.
    #
    # @abstractmethod
    # def __reversed__(self) -> Iterator[SCDILValue]:
    #     ...

    @abstractmethod
    def index(self, value: SCDILValue, start: int = ..., stop: int = ...) -> int:
        ...

    @abstractmethod
    def count(self, value: SCDILValue) -> int:
        ...


@runtime_checkable
class SCDILMapping(Protocol):
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
    @abstractmethod
    def get(self, __key: SCDILValue) -> Optional[SCDILValue]:
        ...

    @overload
    @abstractmethod
    def get(self, __key: SCDILValue, default: T) -> Union[SCDILValue, T]:
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
