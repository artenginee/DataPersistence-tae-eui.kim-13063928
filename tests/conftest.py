import pytest

from src.database.db_manager import DatabaseManager
from src.repositories import SampleRepository, OrderRepository, ProductionJobRepository
from src.models import Sample, Order


@pytest.fixture
def db(tmp_path):
    DatabaseManager._instance = None
    manager = DatabaseManager(str(tmp_path / "test.db"))
    yield manager
    DatabaseManager._instance = None


@pytest.fixture
def sample_repo(db):
    return SampleRepository(db)


@pytest.fixture
def order_repo(db):
    return OrderRepository(db)


@pytest.fixture
def job_repo(db):
    return ProductionJobRepository(db)


@pytest.fixture
def sample(sample_repo):
    return sample_repo.create(Sample("DDR5-16G", 30.0, 0.85, stock=100))


@pytest.fixture
def order(order_repo, sample):
    return order_repo.create(Order("삼성전자", sample.sample_id, 50))
