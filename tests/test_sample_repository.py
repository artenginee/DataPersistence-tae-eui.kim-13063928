import pytest
from src.models import Sample
from src.utils.exceptions import DatabaseError, NotFoundError, ValidationError


class TestSampleRepositoryCreate:
    def test_success_assigns_id_and_timestamps(self, sample_repo):
        s = sample_repo.create(Sample("DDR5", 30.0, 0.85, stock=100))
        assert s.sample_id is not None
        assert s.created_at is not None
        assert s.updated_at is not None

    def test_two_creates_get_different_ids(self, sample_repo):
        s1 = sample_repo.create(Sample("A", 10.0, 0.9))
        s2 = sample_repo.create(Sample("B", 20.0, 0.8))
        assert s1.sample_id != s2.sample_id

    def test_duplicate_name_raises_database_error(self, sample_repo):
        sample_repo.create(Sample("DUP", 10.0, 0.9))
        with pytest.raises(DatabaseError):
            sample_repo.create(Sample("DUP", 20.0, 0.8))

    def test_validation_runs_before_insert(self, sample_repo):
        with pytest.raises(ValidationError):
            sample_repo.create(Sample("", 30.0, 0.85))

    def test_db_exception_wrapped_as_database_error(self, sample_repo, monkeypatch):
        monkeypatch.setattr(sample_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            sample_repo.create(Sample("X", 10.0, 0.9))


class TestSampleRepositoryRead:
    def test_find_by_id_returns_sample(self, sample_repo, sample):
        found = sample_repo.find_by_id(sample.sample_id)
        assert found is not None
        assert found.sample_id == sample.sample_id
        assert found.name == sample.name

    def test_find_by_id_returns_none_when_missing(self, sample_repo):
        assert sample_repo.find_by_id(9999) is None

    def test_find_all_empty(self, sample_repo):
        assert sample_repo.find_all() == []

    def test_find_all_returns_all_in_id_order(self, sample_repo):
        s1 = sample_repo.create(Sample("A", 10.0, 0.9))
        s2 = sample_repo.create(Sample("B", 20.0, 0.8))
        result = sample_repo.find_all()
        assert len(result) == 2
        assert result[0].sample_id == s1.sample_id
        assert result[1].sample_id == s2.sample_id

    def test_find_by_name_exact_match(self, sample_repo):
        sample_repo.create(Sample("DDR5-16G", 30.0, 0.85))
        result = sample_repo.find_by_name("DDR5-16G")
        assert len(result) == 1

    def test_find_by_name_partial_match(self, sample_repo):
        sample_repo.create(Sample("DDR5-16G", 30.0, 0.85))
        sample_repo.create(Sample("DDR5-32G", 40.0, 0.80))
        result = sample_repo.find_by_name("DDR5")
        assert len(result) == 2

    def test_find_by_name_no_match(self, sample_repo):
        sample_repo.create(Sample("DDR5", 30.0, 0.85))
        assert sample_repo.find_by_name("LPDDR") == []

    def test_count_zero(self, sample_repo):
        assert sample_repo.count() == 0

    def test_count_after_inserts(self, sample_repo):
        sample_repo.create(Sample("A", 10.0, 0.9))
        sample_repo.create(Sample("B", 20.0, 0.8))
        assert sample_repo.count() == 2


class TestSampleRepositoryUpdate:
    def test_update_persists_changes(self, sample_repo, sample):
        sample.name = "Updated"
        sample.stock = 999
        sample_repo.update(sample)
        found = sample_repo.find_by_id(sample.sample_id)
        assert found.name == "Updated"
        assert found.stock == 999

    def test_update_refreshes_updated_at(self, sample_repo, sample):
        original_ts = sample.updated_at
        sample.stock = 200
        updated = sample_repo.update(sample)
        assert updated.updated_at >= original_ts

    def test_update_none_id_raises_database_error(self, sample_repo):
        s = Sample("Ghost", 30.0, 0.85)
        with pytest.raises(DatabaseError, match="sample_id"):
            sample_repo.update(s)

    def test_update_validation_error_propagates(self, sample_repo, sample):
        sample.name = ""
        with pytest.raises(ValidationError):
            sample_repo.update(sample)

    def test_update_missing_id_raises_not_found(self, sample_repo):
        s = Sample("Ghost", 30.0, 0.85, sample_id=9999)
        with pytest.raises(NotFoundError):
            sample_repo.update(s)

    def test_update_db_exception_wrapped(self, sample_repo, sample, monkeypatch):
        monkeypatch.setattr(sample_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            sample_repo.update(sample)


class TestSampleRepositoryUpdateStock:
    def test_increase_stock(self, sample_repo, sample):
        new_stock = sample_repo.update_stock(sample.sample_id, 50)
        assert new_stock == 150

    def test_decrease_stock(self, sample_repo, sample):
        new_stock = sample_repo.update_stock(sample.sample_id, -30)
        assert new_stock == 70

    def test_not_found_raises(self, sample_repo):
        with pytest.raises(NotFoundError):
            sample_repo.update_stock(9999, 10)

    def test_db_exception_wrapped(self, sample_repo, sample, monkeypatch):
        monkeypatch.setattr(sample_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            sample_repo.update_stock(sample.sample_id, 10)


class TestSampleRepositoryDelete:
    def test_delete_existing_returns_true(self, sample_repo, sample):
        assert sample_repo.delete(sample.sample_id) is True
        assert sample_repo.find_by_id(sample.sample_id) is None

    def test_delete_missing_returns_false(self, sample_repo):
        assert sample_repo.delete(9999) is False

    def test_db_exception_wrapped(self, sample_repo, monkeypatch):
        monkeypatch.setattr(sample_repo._db, "get_connection", lambda: (_ for _ in ()).throw(Exception("err")))
        with pytest.raises(DatabaseError):
            sample_repo.delete(1)
