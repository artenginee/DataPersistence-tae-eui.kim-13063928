from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderStatus(Enum):
    RESERVED  = "RESERVED"
    REJECTED  = "REJECTED"
    PRODUCING = "PRODUCING"
    CONFIRMED = "CONFIRMED"
    RELEASE   = "RELEASE"


@dataclass
class Order:
    customer_name: str
    sample_id: int
    quantity: int

    order_id: Optional[int] = None
    status: OrderStatus = OrderStatus.RESERVED
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    sample_name: Optional[str] = field(default=None, compare=False, repr=False)

    def validate(self) -> None:
        from src.utils.exceptions import ValidationError
        if not self.customer_name.strip():
            raise ValidationError("customer_name 은 필수입니다.")
        if self.quantity <= 0:
            raise ValidationError("quantity 는 1 이상이어야 합니다.")
