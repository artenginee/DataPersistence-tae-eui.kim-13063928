from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class JobStatus(Enum):
    WAITING     = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED   = "COMPLETED"


@dataclass
class ProductionJob:
    order_id: int
    sample_id: int
    planned_quantity: int
    total_time_min: float

    job_id: Optional[int] = None
    actual_quantity: int = 0
    status: JobStatus = JobStatus.WAITING
    queue_order: int = 0
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    customer_name: Optional[str] = field(default=None, compare=False, repr=False)
    sample_name: Optional[str] = field(default=None, compare=False, repr=False)

    def validate(self) -> None:
        from utils.exceptions import ValidationError
        if self.planned_quantity <= 0:
            raise ValidationError("planned_quantity 는 1 이상이어야 합니다.")
        if self.actual_quantity < 0:
            raise ValidationError("actual_quantity 는 0 이상이어야 합니다.")
