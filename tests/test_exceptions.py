import pytest
from utils.exceptions import NotFoundError, ValidationError, DatabaseError


class TestNotFoundError:
    def test_message_contains_entity_and_id(self):
        err = NotFoundError("Sample", 42)
        assert "Sample" in str(err)
        assert "42" in str(err)

    def test_attributes(self):
        err = NotFoundError("Order", 99)
        assert err.entity == "Order"
        assert err.id_value == 99

    def test_is_exception(self):
        with pytest.raises(NotFoundError):
            raise NotFoundError("X", 1)


class TestValidationError:
    def test_is_exception(self):
        with pytest.raises(ValidationError):
            raise ValidationError("invalid")

    def test_message(self):
        err = ValidationError("field is required")
        assert "field is required" in str(err)


class TestDatabaseError:
    def test_is_exception(self):
        with pytest.raises(DatabaseError):
            raise DatabaseError("db failed")

    def test_message(self):
        err = DatabaseError("connection timeout")
        assert "connection timeout" in str(err)
