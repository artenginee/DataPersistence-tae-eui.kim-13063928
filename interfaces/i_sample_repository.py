from abc import abstractmethod
from typing import List

from repositories.base_repository import BaseRepository
from models.sample import Sample


class ISampleRepository(BaseRepository[Sample]):
    """시료 저장소 인터페이스 — 구체 구현과의 계약을 정의합니다."""

    @abstractmethod
    def find_by_name(self, name: str) -> List[Sample]:
        ...  # pragma: no cover

    @abstractmethod
    def update_stock(self, sample_id: int, delta: int) -> int:
        ...  # pragma: no cover
