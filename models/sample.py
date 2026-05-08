from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Sample:
    name: str
    avg_production_time: float   # 분/개
    yield_rate: float            # 0.0 ~ 1.0

    sample_id: Optional[int] = None
    stock: int = 0
    description: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> None:
        from utils.exceptions import ValidationError
        if not self.name.strip():
            raise ValidationError("name 은 필수입니다.")
        if self.avg_production_time <= 0:
            raise ValidationError("avg_production_time 은 0보다 커야 합니다.")
        if not (0.0 < self.yield_rate <= 1.0):
            raise ValidationError("yield_rate 는 0 초과 1 이하여야 합니다.")
        if self.stock < 0:
            raise ValidationError("stock 은 0 이상이어야 합니다.")
