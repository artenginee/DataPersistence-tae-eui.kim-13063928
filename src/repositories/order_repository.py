from datetime import datetime
from typing import Dict, List, Optional

from src.database.db_manager import DatabaseManager
from src.interfaces.i_order_repository import IOrderRepository
from src.models.order import Order, OrderStatus
from src.utils.exceptions import DatabaseError, NotFoundError


class OrderRepository(IOrderRepository):
    """주문(Order) CRUD — SQLite 구현체"""

    def __init__(self, db: DatabaseManager):
        self._db = db

    # ── CREATE ────────────────────────────────────────────────────────────
    def create(self, entity: Order) -> Order:
        entity.validate()
        sql = """
            INSERT INTO orders (customer_name, sample_id, quantity, status)
            VALUES (?, ?, ?, ?)
        """
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(sql, (
                    entity.customer_name,
                    entity.sample_id,
                    entity.quantity,
                    entity.status.value,
                ))
                entity.order_id = cur.lastrowid
                row = conn.execute(
                    "SELECT created_at, updated_at FROM orders WHERE order_id = ?",
                    (entity.order_id,)
                ).fetchone()
                entity.created_at = datetime.fromisoformat(row["created_at"])
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except Exception as e:
            raise DatabaseError(f"주문 등록 실패: {e}") from e
        return entity

    # ── READ ──────────────────────────────────────────────────────────────
    def find_by_id(self, entity_id: int) -> Optional[Order]:
        row = self._db.query_one(
            _ORDER_JOIN + " WHERE o.order_id = ?", (entity_id,)
        )
        return self._to_order(row) if row else None

    def find_all(self) -> List[Order]:
        rows = self._db.query(_ORDER_JOIN + " ORDER BY o.order_id")
        return [self._to_order(r) for r in rows]

    def find_by_status(self, status: OrderStatus) -> List[Order]:
        rows = self._db.query(
            _ORDER_JOIN + " WHERE o.status = ? ORDER BY o.order_id",
            (status.value,)
        )
        return [self._to_order(r) for r in rows]

    def find_by_sample(self, sample_id: int) -> List[Order]:
        rows = self._db.query(
            _ORDER_JOIN + " WHERE o.sample_id = ? ORDER BY o.order_id",
            (sample_id,)
        )
        return [self._to_order(r) for r in rows]

    def count(self) -> int:
        return self._db.query_one("SELECT COUNT(*) FROM orders")[0]

    def count_by_status(self) -> Dict[str, int]:
        rows = self._db.query("SELECT status, COUNT(*) AS cnt FROM orders GROUP BY status")
        return {r["status"]: r["cnt"] for r in rows}

    # ── UPDATE ────────────────────────────────────────────────────────────
    def update(self, entity: Order) -> Order:
        if entity.order_id is None:
            raise DatabaseError("order_id 가 없어 업데이트할 수 없습니다.")
        entity.validate()
        sql = """
            UPDATE orders
            SET customer_name = ?, sample_id = ?, quantity = ?, status = ?,
                updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
            WHERE order_id = ?
        """
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(sql, (
                    entity.customer_name,
                    entity.sample_id,
                    entity.quantity,
                    entity.status.value,
                    entity.order_id,
                ))
                if cur.rowcount == 0:
                    raise NotFoundError("Order", entity.order_id)
                row = conn.execute(
                    "SELECT updated_at FROM orders WHERE order_id = ?",
                    (entity.order_id,)
                ).fetchone()
                entity.updated_at = datetime.fromisoformat(row["updated_at"])
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"주문 수정 실패: {e}") from e
        return entity

    def update_status(self, order_id: int, status: OrderStatus) -> bool:
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute(
                    """UPDATE orders SET status = ?,
                       updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')
                       WHERE order_id = ?""",
                    (status.value, order_id)
                )
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"주문 상태 변경 실패: {e}") from e

    # ── DELETE ────────────────────────────────────────────────────────────
    def delete(self, entity_id: int) -> bool:
        try:
            with self._db.get_connection() as conn:
                cur = conn.execute("DELETE FROM orders WHERE order_id = ?", (entity_id,))
                return cur.rowcount > 0
        except Exception as e:
            raise DatabaseError(f"주문 삭제 실패: {e}") from e

    # ── 내부 변환 ─────────────────────────────────────────────────────────
    @staticmethod
    def _to_order(row) -> Order:
        return Order(
            order_id=row["order_id"],
            customer_name=row["customer_name"],
            sample_id=row["sample_id"],
            quantity=row["quantity"],
            status=OrderStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            sample_name=row["sample_name"],
        )


_ORDER_JOIN = """
    SELECT o.*, s.name AS sample_name
    FROM orders o
    LEFT JOIN samples s ON o.sample_id = s.sample_id
"""
