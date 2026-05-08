from abc import abstractmethod
from typing import Dict, List

from repositories.base_repository import BaseRepository
from models.order import Order, OrderStatus


class IOrderRepository(BaseRepository[Order]):
    """주문 저장소 인터페이스 — 구체 구현과의 계약을 정의합니다."""

    @abstractmethod
    def find_by_status(self, status: OrderStatus) -> List[Order]:
        ...  # pragma: no cover

    @abstractmethod
    def find_by_sample(self, sample_id: int) -> List[Order]:
        ...  # pragma: no cover

    @abstractmethod
    def count_by_status(self) -> Dict[str, int]:
        ...  # pragma: no cover

    @abstractmethod
    def update_status(self, order_id: int, status: OrderStatus) -> bool:
        ...  # pragma: no cover
