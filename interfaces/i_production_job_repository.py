from abc import abstractmethod
from typing import Dict, List, Optional

from repositories.base_repository import BaseRepository
from models.production_job import ProductionJob, JobStatus


class IProductionJobRepository(BaseRepository[ProductionJob]):
    """생산 작업 큐 저장소 인터페이스 — 구체 구현과의 계약을 정의합니다."""

    @abstractmethod
    def find_by_status(self, status: JobStatus) -> List[ProductionJob]:
        ...  # pragma: no cover

    @abstractmethod
    def find_waiting_queue(self) -> List[ProductionJob]:
        ...  # pragma: no cover

    @abstractmethod
    def find_in_progress(self) -> Optional[ProductionJob]:
        ...  # pragma: no cover

    @abstractmethod
    def find_by_order(self, order_id: int) -> Optional[ProductionJob]:
        ...  # pragma: no cover

    @abstractmethod
    def count_by_status(self) -> Dict[str, int]:
        ...  # pragma: no cover

    @abstractmethod
    def update_status(self, job_id: int, status: JobStatus) -> bool:
        ...  # pragma: no cover

    @abstractmethod
    def update_actual_quantity(self, job_id: int, actual_quantity: int) -> bool:
        ...  # pragma: no cover
