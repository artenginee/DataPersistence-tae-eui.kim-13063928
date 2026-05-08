import pytest
from src.models import ProductionJob, JobStatus
from src.utils.exceptions import DatabaseError, NotFoundError, ValidationError


def _job(order_id: int, sample_id: int, **kwargs) -> ProductionJob:
    return ProductionJob(order_id=order_id, sample_id=sample_id,
                         planned_quantity=kwargs.get("planned_quantity", 100),
                         total_time_min=kwargs.get("total_time_min", 300.0),
                         **{k: v for k, v in kwargs.items()
                            if k not in ("planned_quantity", "total_time_min")})


class TestProductionJobRepositoryCreate:
    def test_success_assigns_id_and_timestamps(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        assert j.job_id is not None
        assert j.created_at is not None
        assert j.updated_at is not None

    def test_first_job_gets_queue_order_one(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        assert j.queue_order == 1

    def test_queue_order_increments_fifo(self, job_repo, order, sample):
        j1 = job_repo.create(_job(order.order_id, sample.sample_id))
        j2 = job_repo.create(_job(order.order_id, sample.sample_id))
        assert j2.queue_order == j1.queue_order + 1

    def test_validation_runs_before_insert(self, job_repo, order, sample):
        with pytest.raises(ValidationError):
            job_repo.create(_job(order.order_id, sample.sample_id, planned_quantity=0))

    def test_db_exception_wrapped(self, job_repo, order, sample, monkeypatch):
        monkeypatch.setattr(job_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            job_repo.create(_job(order.order_id, sample.sample_id))


class TestProductionJobRepositoryRead:
    def test_find_by_id_returns_job_with_joins(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        found = job_repo.find_by_id(j.job_id)
        assert found is not None
        assert found.customer_name == order.customer_name
        assert found.sample_name == sample.name

    def test_find_by_id_returns_none_when_missing(self, job_repo):
        assert job_repo.find_by_id(9999) is None

    def test_find_all_empty(self, job_repo):
        assert job_repo.find_all() == []

    def test_find_all_in_fifo_order(self, job_repo, order, sample):
        j1 = job_repo.create(_job(order.order_id, sample.sample_id))
        j2 = job_repo.create(_job(order.order_id, sample.sample_id))
        result = job_repo.find_all()
        assert result[0].queue_order < result[1].queue_order
        assert result[0].job_id == j1.job_id

    def test_find_by_status_waiting(self, job_repo, order, sample):
        job_repo.create(_job(order.order_id, sample.sample_id))
        result = job_repo.find_by_status(JobStatus.WAITING)
        assert len(result) == 1
        assert result[0].status == JobStatus.WAITING

    def test_find_by_status_empty(self, job_repo):
        assert job_repo.find_by_status(JobStatus.COMPLETED) == []

    def test_find_waiting_queue_returns_waiting_jobs(self, job_repo, order, sample):
        job_repo.create(_job(order.order_id, sample.sample_id))
        result = job_repo.find_waiting_queue()
        assert len(result) == 1

    def test_find_in_progress_returns_none_when_none(self, job_repo):
        assert job_repo.find_in_progress() is None

    def test_find_in_progress_returns_job(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        job_repo.update_status(j.job_id, JobStatus.IN_PROGRESS)
        found = job_repo.find_in_progress()
        assert found is not None
        assert found.status == JobStatus.IN_PROGRESS

    def test_find_by_order_returns_job(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        found = job_repo.find_by_order(order.order_id)
        assert found is not None
        assert found.job_id == j.job_id

    def test_find_by_order_returns_none_when_missing(self, job_repo):
        assert job_repo.find_by_order(9999) is None

    def test_count_zero(self, job_repo):
        assert job_repo.count() == 0

    def test_count_after_inserts(self, job_repo, order, sample):
        job_repo.create(_job(order.order_id, sample.sample_id))
        job_repo.create(_job(order.order_id, sample.sample_id))
        assert job_repo.count() == 2

    def test_count_by_status(self, job_repo, order, sample):
        job_repo.create(_job(order.order_id, sample.sample_id))
        counts = job_repo.count_by_status()
        assert counts.get("WAITING", 0) == 1

    def test_count_by_status_empty(self, job_repo):
        assert job_repo.count_by_status() == {}


class TestProductionJobRepositoryUpdate:
    def test_update_persists_changes(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        j.planned_quantity = 500
        j.notes = "updated"
        job_repo.update(j)
        found = job_repo.find_by_id(j.job_id)
        assert found.planned_quantity == 500
        assert found.notes == "updated"

    def test_update_refreshes_updated_at(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        original_ts = j.updated_at
        j.planned_quantity = 200
        updated = job_repo.update(j)
        assert updated.updated_at >= original_ts

    def test_update_none_id_raises_database_error(self, job_repo):
        j = ProductionJob(1, 1, 100, 300.0)
        with pytest.raises(DatabaseError, match="job_id"):
            job_repo.update(j)

    def test_update_validation_error_propagates(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        j.planned_quantity = 0
        with pytest.raises(ValidationError):
            job_repo.update(j)

    def test_update_missing_id_raises_not_found(self, job_repo):
        j = ProductionJob(1, 1, 100, 300.0, job_id=9999)
        with pytest.raises(NotFoundError):
            job_repo.update(j)

    def test_update_db_exception_wrapped(self, job_repo, order, sample, monkeypatch):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        monkeypatch.setattr(job_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            job_repo.update(j)

    def test_update_status_success(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        result = job_repo.update_status(j.job_id, JobStatus.IN_PROGRESS)
        assert result is True
        found = job_repo.find_by_id(j.job_id)
        assert found.status == JobStatus.IN_PROGRESS

    def test_update_status_not_found(self, job_repo):
        result = job_repo.update_status(9999, JobStatus.COMPLETED)
        assert result is False

    def test_update_status_db_exception_wrapped(self, job_repo, monkeypatch):
        monkeypatch.setattr(job_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            job_repo.update_status(1, JobStatus.COMPLETED)

    def test_update_actual_quantity_success(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        result = job_repo.update_actual_quantity(j.job_id, 80)
        assert result is True
        found = job_repo.find_by_id(j.job_id)
        assert found.actual_quantity == 80

    def test_update_actual_quantity_not_found(self, job_repo):
        result = job_repo.update_actual_quantity(9999, 10)
        assert result is False

    def test_update_actual_quantity_negative_raises(self, job_repo):
        with pytest.raises(DatabaseError, match="actual_quantity"):
            job_repo.update_actual_quantity(1, -1)

    def test_update_actual_quantity_db_exception_wrapped(self, job_repo, monkeypatch):
        monkeypatch.setattr(job_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            job_repo.update_actual_quantity(1, 10)


class TestProductionJobRepositoryDelete:
    def test_delete_existing_returns_true(self, job_repo, order, sample):
        j = job_repo.create(_job(order.order_id, sample.sample_id))
        assert job_repo.delete(j.job_id) is True
        assert job_repo.find_by_id(j.job_id) is None

    def test_delete_missing_returns_false(self, job_repo):
        assert job_repo.delete(9999) is False

    def test_db_exception_wrapped(self, job_repo, monkeypatch):
        monkeypatch.setattr(job_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            job_repo.delete(1)
