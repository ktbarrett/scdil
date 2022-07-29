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
# Sequence and Mapping are a workaround
#
# Value = Union[None, bool, int, float, str, "Sequence[Value]", "Mapping[Value, Value]"]
Value = Union[None, bool, int, float, str, "Sequence", "Mapping"]


@runtime_checkable
class Sequence(Protocol):
    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, item: int) -> Value:
        ...

    @overload
    @abstractmethod
    def __getitem__(self, item: slice) -> "Sequence":
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Value]:
        ...

    # tuple does not have a public __reversed__ method, but implements reversed() in some special way.
    # We don't really need reversed() for this library to function, so we will leave this out for now.
    #
    # @abstractmethod
    # def __reversed__(self) -> Iterator[SCDILValue]:
    #     ...

    @abstractmethod
    def index(self, value: Value, start: int = ..., stop: int = ...) -> int:
        ...

    @abstractmethod
    def count(self, value: Value) -> int:
        ...


@runtime_checkable
class Mapping(Protocol):
    @abstractmethod
    def __len__(self) -> int:
        ...

    @abstractmethod
    def __contains__(self, item: object) -> bool:
        ...

    @abstractmethod
    def __getitem__(self, item: Value) -> Value:
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[Value]:
        ...

    @overload
    @abstractmethod
    def get(self, __key: Value) -> Optional[Value]:
        ...

    @overload
    @abstractmethod
    def get(self, __key: Value, default: T) -> Union[Value, T]:
        ...

    @abstractmethod
    def keys(self) -> KeysView[Value]:
        ...

    @abstractmethod
    def values(self) -> ValuesView[Value]:
        ...

    @abstractmethod
    def items(self) -> ItemsView[Value, Value]:
        ...
