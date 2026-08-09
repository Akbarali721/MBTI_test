"""payment_requests: sessiyaga bitta faol to'lov (partial unique index)

Revision ID: 009_active_payment
Revises: 008_enum_repair

Ilova qatlami allaqachon "bitta faol to'lov" qoidasini tekshiradi, lekin veb va bot
alohida jarayonlar bo'lgani uchun tekshiruv poyga holatiga ochiq. Bu indeks qoidani
baza darajasida majburiy qiladi.
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect, text

revision: str = "009_active_payment"
down_revision: Union[str, None] = "008_enum_repair"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLE = "payment_requests"
INDEX_NAME = "uq_payment_requests_active_session"
ACTIVE_STATUSES = ("pending", "receipt_sent")


def _bind():
    return op.get_bind()


def _dialect_name() -> str:
    return _bind().dialect.name


def _has_table(table_name: str) -> bool:
    return table_name in inspect(_bind()).get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in {col["name"] for col in inspect(_bind()).get_columns(table_name)}


def _has_index(table_name: str, name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(ix["name"] == name for ix in inspect(_bind()).get_indexes(table_name))


def _status_list_sql() -> str:
    return ", ".join(f"'{status}'" for status in ACTIVE_STATUSES)


def _has_active_duplicate_rows() -> bool:
    row = _bind().execute(
        text(
            f"""
            SELECT 1
              FROM {TABLE}
             WHERE status IN ({_status_list_sql()})
             GROUP BY session_id
            HAVING COUNT(*) > 1
             LIMIT 1
            """
        )
    ).first()
    return row is not None


def _deduplicate_active_payments() -> None:
    """Keep newest active row per session; mark older actives rejected (no deletes)."""
    if not _has_active_duplicate_rows():
        return

    status_sql = _status_list_sql()
    if _dialect_name() == "postgresql":
        _bind().execute(
            text(
                f"""
                WITH ranked AS (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY session_id ORDER BY id DESC
                           ) AS rn
                      FROM {TABLE}
                     WHERE status IN ({status_sql})
                )
                UPDATE {TABLE} AS pr
                   SET status = 'rejected'
                  FROM ranked AS r
                 WHERE pr.id = r.id
                   AND r.rn > 1
                """
            )
        )
        return

    _bind().execute(
        text(
            f"""
            UPDATE {TABLE}
               SET status = 'rejected'
             WHERE status IN ({status_sql})
               AND id NOT IN (
                     SELECT MAX(id) FROM {TABLE}
                      WHERE status IN ({status_sql})
                      GROUP BY session_id
                   )
            """
        )
    )


def _create_partial_unique_index() -> None:
    where_sql = f"status IN ({_status_list_sql()})"
    if _dialect_name() == "postgresql":
        _bind().execute(
            text(
                f"""
                CREATE UNIQUE INDEX IF NOT EXISTS {INDEX_NAME}
                    ON {TABLE} (session_id)
                 WHERE {where_sql}
                """
            )
        )
        return

    op.create_index(
        INDEX_NAME,
        TABLE,
        ["session_id"],
        unique=True,
        sqlite_where=text(where_sql),
    )


def upgrade() -> None:
    if not _has_table(TABLE):
        return
    if not _has_column(TABLE, "session_id") or not _has_column(TABLE, "status"):
        return
    if _has_index(TABLE, INDEX_NAME):
        return

    _deduplicate_active_payments()
    if _has_active_duplicate_rows():
        raise RuntimeError(
            f"{TABLE}: duplicate active payment rows remain after deduplication; "
            f"cannot create partial unique index {INDEX_NAME!r}"
        )
    _create_partial_unique_index()


def downgrade() -> None:
    if not _has_table(TABLE):
        return
    if not _has_index(TABLE, INDEX_NAME):
        return
    if _dialect_name() == "postgresql":
        _bind().execute(text(f"DROP INDEX IF EXISTS {INDEX_NAME}"))
        return
    op.drop_index(INDEX_NAME, table_name=TABLE)
