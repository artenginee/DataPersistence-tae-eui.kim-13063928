from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """모든 저장소가 구현해야 하는 기본 CRUD 인터페이스."""

    @abstractmethod
    def create(self, entity: T) -> T:
        ...  # pragma: no cover

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[T]:
        ...  # pragma: no cover

    @abstractmethod
    def find_all(self) -> List[T]:
        ...  # pragma: no cover

    @abstractmethod
    def update(self, entity: T) -> T:
        ...  # pragma: no cover

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        ...  # pragma: no cover

    @abstractmethod
    def count(self) -> int:
        ...  # pragma: no cover
