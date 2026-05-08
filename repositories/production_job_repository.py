from datetime import datetime
from typing import Dict, List, Optional

from database.db_manager import DatabaseManager
from interfaces.i_production_job_repository import IProductionJobRepository
from models.production_job import ProductionJob, JobStatus
from utils.exceptions import DatabaseError, NotFoundError


class ProductionJobRepository(IProductionJobRepository):
    """생산 작업 큐(ProductionJob) CRUD — SQLite 구현체 (FIFO)"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    # ── CREATE ────────────────────────────────────────────────────────────
    def create(self, entity: ProductionJob) -> ProductionJob:
        entity.validate()
        sql = """
            INSERT INTO production_jobs
                (order_id, sample_id, planned_quantity, actual_quantity,
                 total_time_min, status, queue_order, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._db.get_connection() as conn:
                max_row = conn.execute(
                    "SELECT COALESCE(MAX(queue_order), 0) FROM production_jobs"
                ).fetchone()
                entity.queue_order = max_row[0] + 1
                cur = conn.execute(sql, (
                    entity.order_id,
                    entity.sample_id,
                    entity.planned_quantity,
                    entity.actual_quantity,
                    entity.total_time_min,
                    entity.status.value,
                    entity.queue_order,
                    entity.notes,
                ))
                entity.job_id = cur.lastrowid
                row = conn.execute(
                    "SELECT created_at, updated_at FROM production_jobs WHERE job_id = ?",
                    (entity.job_id,)
                ).fetchone()
                entity.created_at = datetime.fromisoformat(row["created_at"])
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except Exception as e:
            raise DatabaseError(f"생산 작업 등록 실패: {e}") from e
        return entity

    # ── READ ──────────────────────────────────────────────────────────────
    def find_by_id(self, entity_id: int) -> Optional[ProductionJob]:
        row = self._db.query_one(_JOB_JOIN + " WHERE j.job_id = ?", (entity_id,))
        return self._to_job(row) if row else None

    def find_all(self) -> List[ProductionJob]:
        rows = self._db.query(_JOB_JOIN + " ORDER BY j.queue_order")
        return [self._to_job(r) for r in rows]

    def find_by_status(self, status: JobStatus) -> List[ProductionJob]:
        rows = self._db.query(
            _JOB_JOIN + " WHERE j.status = ? ORDER BY j.queue_order",
            (status.value,)
        )
        return [self._to_job(r) for r in rows]

    def find_waiting_queue(self) -> List[ProductionJob]:
        return self.find_by_status(JobStatus.WAITING)

    def find_in_progress(self) -> Optional[ProductionJob]:
        row = self._db.query_one(_JOB_JOIN + " WHERE j.status = 'IN_PROGRESS' LIMIT 1")
        return self._to_job(row) if row else None

    def find_by_order(self, order_id: int) -> Optional[ProductionJob]:
        row = self._db.query_one(
            _JOB_JOIN + " WHERE j.order_id = ? LIMIT 1", (order_id,)
        )
        return self._to_job(row) if row else None

    def count(self) -> int:
        return self._db.query_one("SELECT COUNT(*) FROM production_jobs")[0]

    def count_by_status(self) -> Dict[str, int]:
        rows = self._db.query(
            "SELECT status, COUNT(*) AS cnt FROM production_jobs GROUP BY status"
        )
        return {r["status"]: r["cnt"] for r in rows}

    # ── UPDATE ────────────────────────────────────────────────────────────
    def update(self, entity: ProductionJob) -> ProductionJob:
        if entity.job_id is None:
            raise DatabaseError("job_id 가 없어 업데이트할 수 없습니다.")
        entity.validate()
        sql = """
            UPDATE production_jobs
            SET order_id = ?, sample_id = ?, planned_quantity = ?,
                actual_quantity = ?, total_time_min = ?, status = ?,
                queue_order = ?, notes = ?,
                updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
            WHERE job_id = ?
        """
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(sql, (
                    entity.order_id,
                    entity.sample_id,
                    entity.planned_quantity,
                    entity.actual_quantity,
                    entity.total_time_min,
                    entity.status.value,
                    entity.queue_order,
                    entity.notes,
                    entity.job_id,
                ))
                if cur.rowcount == 0:
                    raise NotFoundError("ProductionJob", entity.job_id)
                row = conn.execute(
                    "SELECT updated_at FROM production_jobs WHERE job_id = ?",
                    (entity.job_id,)
                ).fetchone()
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"생산 작업 수정 실패: {e}") from e
        return entity

    def update_status(self, job_id: int, status: JobStatus) -> bool:
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(
                    """UPDATE production_jobs SET status = ?,
                       updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                       WHERE job_id = ?""",
                    (status.value, job_id)
                )
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"생산 상태 변경 실패: {e}") from e

    def update_actual_quantity(self, job_id: int, actual_quantity: int) -> bool:
        if actual_quantity < 0:
            raise DatabaseError("actual_quantity 는 0 이상이어야 합니다.")
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(
                    """UPDATE production_jobs SET actual_quantity = ?,
                       updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                       WHERE job_id = ?""",
                    (actual_quantity, job_id)
                )
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"실적 수량 업데이트 실패: {e}") from e

    # ── DELETE ────────────────────────────────────────────────────────────
    def delete(self, entity_id: int) -> bool:
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(
                    "DELETE FROM production_jobs WHERE job_id = ?", (entity_id,)
                )
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"생산 작업 삭제 실패: {e}") from e

    # ── 내부 변환 ─────────────────────────────────────────────────────────
    @staticmethod
    def _to_job(row) -> ProductionJob:
        return ProductionJob(
            job_id=row["job_id"],
            order_id=row["order_id"],
            sample_id=row["sample_id"],
            planned_quantity=row["planned_quantity"],
            actual_quantity=row["actual_quantity"],
            total_time_min=row["total_time_min"],
            status=JobStatus(row["status"]),
            queue_order=row["queue_order"],
            notes=row["notes"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            customer_name=row["customer_name"],
            sample_name=row["sample_name"],
        )


_JOB_JOIN = """
    SELECT j.*,
           o.customer_name,
           s.name AS sample_name
    FROM production_jobs j
    LEFT JOIN orders   o ON j.order_id  = o.order_id
    LEFT JOIN samples  s ON j.sample_id = s.sample_id
"""
