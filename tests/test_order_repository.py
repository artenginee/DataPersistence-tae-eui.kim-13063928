import pytest
from models import Order, OrderStatus
from utils.exceptions import DatabaseError, NotFoundError, ValidationError


class TestOrderRepositoryCreate:
    def test_success_assigns_id_and_timestamps(self, order_repo, sample):
        o = order_repo.create(Order("고객A", sample.sample_id, 10))
        assert o.order_id is not None
        assert o.created_at is not None
        assert o.updated_at is not None

    def test_default_status_is_reserved(self, order_repo, sample):
        o = order_repo.create(Order("고객A", sample.sample_id, 10))
        assert o.status == OrderStatus.RESERVED

    def test_fk_violation_raises_database_error(self, order_repo):
        with pytest.raises(DatabaseError):
            order_repo.create(Order("고객A", 9999, 10))

    def test_validation_runs_before_insert(self, order_repo, sample):
        with pytest.raises(ValidationError):
            order_repo.create(Order("", sample.sample_id, 10))

    def test_db_exception_wrapped(self, order_repo, sample, monkeypatch):
        monkeypatch.setattr(order_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            order_repo.create(Order("고객A", sample.sample_id, 10))


class TestOrderRepositoryRead:
    def test_find_by_id_returns_order_with_sample_name(self, order_repo, order, sample):
        found = order_repo.find_by_id(order.order_id)
        assert found is not None
        assert found.order_id == order.order_id
        assert found.sample_name == sample.name

    def test_find_by_id_returns_none_when_missing(self, order_repo):
        assert order_repo.find_by_id(9999) is None

    def test_find_all_empty(self, order_repo):
        assert order_repo.find_all() == []

    def test_find_all_returns_all_in_id_order(self, order_repo, sample):
        o1 = order_repo.create(Order("A", sample.sample_id, 10))
        o2 = order_repo.create(Order("B", sample.sample_id, 20))
        result = order_repo.find_all()
        assert len(result) == 2
        assert result[0].order_id == o1.order_id
        assert result[1].order_id == o2.order_id

    def test_find_by_status_reserved(self, order_repo, sample):
        order_repo.create(Order("고객A", sample.sample_id, 10))
        result = order_repo.find_by_status(OrderStatus.RESERVED)
        assert len(result) == 1
        assert result[0].status == OrderStatus.RESERVED

    def test_find_by_status_empty(self, order_repo):
        result = order_repo.find_by_status(OrderStatus.CONFIRMED)
        assert result == []

    def test_find_by_sample(self, order_repo, sample):
        order_repo.create(Order("고객A", sample.sample_id, 10))
        order_repo.create(Order("고객B", sample.sample_id, 20))
        result = order_repo.find_by_sample(sample.sample_id)
        assert len(result) == 2

    def test_find_by_sample_empty(self, order_repo):
        assert order_repo.find_by_sample(9999) == []

    def test_count_zero(self, order_repo):
        assert order_repo.count() == 0

    def test_count_after_inserts(self, order_repo, sample):
        order_repo.create(Order("A", sample.sample_id, 10))
        order_repo.create(Order("B", sample.sample_id, 20))
        assert order_repo.count() == 2

    def test_count_by_status(self, order_repo, sample):
        order_repo.create(Order("A", sample.sample_id, 10))
        order_repo.create(Order("B", sample.sample_id, 20))
        counts = order_repo.count_by_status()
        assert counts.get("RESERVED", 0) == 2

    def test_count_by_status_empty(self, order_repo):
        assert order_repo.count_by_status() == {}


class TestOrderRepositoryUpdate:
    def test_update_persists_changes(self, order_repo, order):
        order.customer_name = "변경고객"
        order.quantity = 999
        order_repo.update(order)
        found = order_repo.find_by_id(order.order_id)
        assert found.customer_name == "변경고객"
        assert found.quantity == 999

    def test_update_refreshes_updated_at(self, order_repo, order):
        original_ts = order.updated_at
        order.quantity = 1
        updated = order_repo.update(order)
        assert updated.updated_at >= original_ts

    def test_update_none_id_raises_database_error(self, order_repo):
        o = Order("고객A", 1, 10)
        with pytest.raises(DatabaseError, match="order_id"):
            order_repo.update(o)

    def test_update_validation_error_propagates(self, order_repo, order):
        order.customer_name = ""
        with pytest.raises(ValidationError):
            order_repo.update(order)

    def test_update_missing_id_raises_not_found(self, order_repo, sample):
        o = Order("고객A", sample.sample_id, 10, order_id=9999)
        with pytest.raises(NotFoundError):
            order_repo.update(o)

    def test_update_db_exception_wrapped(self, order_repo, order, monkeypatch):
        monkeypatch.setattr(order_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            order_repo.update(order)

    def test_update_status_success(self, order_repo, order):
        result = order_repo.update_status(order.order_id, OrderStatus.CONFIRMED)
        assert result is True
        found = order_repo.find_by_id(order.order_id)
        assert found.status == OrderStatus.CONFIRMED

    def test_update_status_not_found(self, order_repo):
        result = order_repo.update_status(9999, OrderStatus.CONFIRMED)
        assert result is False

    def test_update_status_db_exception_wrapped(self, order_repo, monkeypatch):
        monkeypatch.setattr(order_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            order_repo.update_status(1, OrderStatus.CONFIRMED)


class TestOrderRepositoryDelete:
    def test_delete_existing_returns_true(self, order_repo, order):
        assert order_repo.delete(order.order_id) is True
        assert order_repo.find_by_id(order.order_id) is None

    def test_delete_missing_returns_false(self, order_repo):
        assert order_repo.delete(9999) is False

    def test_db_exception_wrapped(self, order_repo, monkeypatch):
        monkeypatch.setattr(order_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            order_repo.delete(1)
