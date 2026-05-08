from datetime import datetime
from typing import List, Optional

from src.database.db_manager import DatabaseManager
from src.interfaces.i_sample_repository import ISampleRepository
from src.models.sample import Sample
from src.utils.exceptions import DatabaseError, NotFoundError


class SampleRepository(ISampleRepository):
    """시료(Sample) CRUD — SQLite 구현체"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    # ── CREATE ────────────────────────────────────────────────────────────
    def create(self, entity: Sample) -> Sample:
        entity.validate()
        sql = """
            INSERT INTO samples (name, avg_production_time, yield_rate, stock, description)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(sql, (
                    entity.name,
                    entity.avg_production_time,
                    entity.yield_rate,
                    entity.stock,
                    entity.description,
                ))
                entity.sample_id = cur.lastrowid
                row = conn.execute(
                    "SELECT created_at, updated_at FROM samples WHERE sample_id = ?",
                    (entity.sample_id,)
                ).fetchone()
                entity.created_at = datetime.fromisoformat(row["created_at"])
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except Exception as e:
            raise DatabaseError(f"시료 등록 실패: {e}") from e
        return entity

    # ── READ ──────────────────────────────────────────────────────────────
    def find_by_id(self, entity_id: int) -> Optional[Sample]:
        row = self._db.query_one(
            "SELECT * FROM samples WHERE sample_id = ?", (entity_id,)
        )
        return self._to_sample(row) if row else None

    def find_all(self) -> List[Sample]:
        rows = self._db.query("SELECT * FROM samples ORDER BY sample_id")
        return [self._to_sample(r) for r in rows]

    def find_by_name(self, name: str) -> List[Sample]:
        rows = self._db.query(
            "SELECT * FROM samples WHERE name LIKE ? ORDER BY sample_id",
            (f"%{name}%",)
        )
        return [self._to_sample(r) for r in rows]

    def count(self) -> int:
        return self._db.query_one("SELECT COUNT(*) FROM samples")[0]

    # ── UPDATE ────────────────────────────────────────────────────────────
    def update(self, entity: Sample) -> Sample:
        if entity.sample_id is None:
            raise DatabaseError("sample_id 가 없어 업데이트할 수 없습니다.")
        entity.validate()
        sql = """
            UPDATE samples
            SET name = ?, avg_production_time = ?, yield_rate = ?,
                stock = ?, description = ?,
                updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
            WHERE sample_id = ?
        """
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(sql, (
                    entity.name,
                    entity.avg_production_time,
                    entity.yield_rate,
                    entity.stock,
                    entity.description,
                    entity.sample_id,
                ))
                if cur.rowcount == 0:
                    raise NotFoundError("Sample", entity.sample_id)
                row = conn.execute(
                    "SELECT updated_at FROM samples WHERE sample_id = ?",
                    (entity.sample_id,)
                ).fetchone()
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"시료 수정 실패: {e}") from e
        return entity

    def update_stock(self, sample_id: int, delta: int) -> int:
        try:
            with self._db.get_connection() as conn:
                conn.execute(
                    """UPDATE samples
                       SET stock = stock + ?,
                           updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                       WHERE sample_id = ?""",
                    (delta, sample_id)
                )
                row = conn.execute(
                    "SELECT stock FROM samples WHERE sample_id = ?", (sample_id,)
                ).fetchone()
                if row is None:
                    raise NotFoundError("Sample", sample_id)
                return row["stock"]
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"재고 업데이트 실패: {e}") from e

    # ── DELETE ────────────────────────────────────────────────────────────
    def delete(self, entity_id: int) -> bool:
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(
                    "DELETE FROM samples WHERE sample_id = ?", (entity_id,)
                )
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"시료 삭제 실패: {e}") from e

    # ── 내부 변환 ─────────────────────────────────────────────────────────
    @staticmethod
    def _to_sample(row) -> Sample:
        return Sample(
            sample_id=row["sample_id"],
            name=row["name"],
            avg_production_time=row["avg_production_time"],
            yield_rate=row["yield_rate"],
            stock=row["stock"],
            description=row["description"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
