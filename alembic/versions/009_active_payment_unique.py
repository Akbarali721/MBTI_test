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


def _has_table(table_name: str) -> bool:
    return table_name in inspect(op.get_bind()).get_table_names()


def _has_index(table_name: str, name: str) -> bool:
    return any(ix["name"] == name for ix in inspect(op.get_bind()).get_indexes(table_name))


def _status_list() -> str:
    return ", ".join(f"'{status}'" for status in ACTIVE_STATUSES)


def _deduplicate_active_payments() -> None:
    """Indeks yaratishdan oldin sessiyada bittadan ortiq faol qator qolmasligi kerak.

    Eng so'nggi faol yozuv saqlanadi, eskilari rad etilgan deb belgilanadi — o'chirilmaydi,
    chunki ular to'lov tarixining bir qismi.
    """
    op.get_bind().execute(
        text(
            f"""
            UPDATE {TABLE}
               SET status = 'rejected'
             WHERE status IN ({_status_list()})
               AND id NOT IN (
                     SELECT MAX(id) FROM {TABLE}
                      WHERE status IN ({_status_list()})
                      GROUP BY session_id
                   )
            """
        )
    )


def upgrade() -> None:
    if not _has_table(TABLE) or _has_index(TABLE, INDEX_NAME):
        return
    _deduplicate_active_payments()
    op.create_index(
        INDEX_NAME,
        TABLE,
        ["session_id"],
        unique=True,
        sqlite_where=text(f"status IN ({_status_list()})"),
        postgresql_where=text(f"status IN ({_status_list()})"),
    )


def downgrade() -> None:
    if _has_table(TABLE) and _has_index(TABLE, INDEX_NAME):
        op.drop_index(INDEX_NAME, table_name=TABLE)
