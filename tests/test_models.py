import pytest
from src.models import Sample, Order, OrderStatus, ProductionJob, JobStatus
from src.utils.exceptions import ValidationError


class TestSampleValidate:
    def test_valid(self):
        Sample("DDR5", 30.0, 0.85, stock=0).validate()

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError, match="name"):
            Sample("", 30.0, 0.85).validate()

    def test_whitespace_name_raises(self):
        with pytest.raises(ValidationError, match="name"):
            Sample("   ", 30.0, 0.85).validate()

    def test_zero_production_time_raises(self):
        with pytest.raises(ValidationError, match="avg_production_time"):
            Sample("X", 0.0, 0.85).validate()

    def test_negative_production_time_raises(self):
        with pytest.raises(ValidationError, match="avg_production_time"):
            Sample("X", -1.0, 0.85).validate()

    def test_zero_yield_rate_raises(self):
        with pytest.raises(ValidationError, match="yield_rate"):
            Sample("X", 30.0, 0.0).validate()

    def test_yield_rate_above_one_raises(self):
        with pytest.raises(ValidationError, match="yield_rate"):
            Sample("X", 30.0, 1.01).validate()

    def test_yield_rate_exactly_one_is_valid(self):
        Sample("X", 30.0, 1.0).validate()

    def test_negative_stock_raises(self):
        with pytest.raises(ValidationError, match="stock"):
            Sample("X", 30.0, 0.85, stock=-1).validate()


class TestOrderStatusEnum:
    def test_all_values_exist(self):
        assert OrderStatus.RESERVED.value  == "RESERVED"
        assert OrderStatus.REJECTED.value  == "REJECTED"
        assert OrderStatus.PRODUCING.value == "PRODUCING"
        assert OrderStatus.CONFIRMED.value == "CONFIRMED"
        assert OrderStatus.RELEASE.value   == "RELEASE"


class TestOrderValidate:
    def test_valid(self):
        Order("고객A", 1, 10).validate()

    def test_empty_customer_name_raises(self):
        with pytest.raises(ValidationError, match="customer_name"):
            Order("", 1, 10).validate()

    def test_zero_quantity_raises(self):
        with pytest.raises(ValidationError, match="quantity"):
            Order("고객A", 1, 0).validate()

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError, match="quantity"):
            Order("고객A", 1, -5).validate()


class TestJobStatusEnum:
    def test_all_values_exist(self):
        assert JobStatus.WAITING.value     == "WAITING"
        assert JobStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert JobStatus.COMPLETED.value   == "COMPLETED"


class TestProductionJobValidate:
    def test_valid(self):
        ProductionJob(1, 1, 100, 300.0).validate()

    def test_zero_planned_quantity_raises(self):
        with pytest.raises(ValidationError, match="planned_quantity"):
            ProductionJob(1, 1, 0, 300.0).validate()

    def test_negative_planned_quantity_raises(self):
        with pytest.raises(ValidationError, match="planned_quantity"):
            ProductionJob(1, 1, -1, 300.0).validate()

    def test_negative_actual_quantity_raises(self):
        with pytest.raises(ValidationError, match="actual_quantity"):
            ProductionJob(1, 1, 100, 300.0, actual_quantity=-1).validate()
