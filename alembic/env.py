import sqlite3
from logging.config import fileConfig

from sqlalchemy import engine_from_config, event, pool

from alembic import context

# Paket `__init__` barcha modellarni import qiladi — autogenerate to'liq metadata ko'rishi
# uchun aynan shu import kerak (alohida modullarni sanash bittasini unutishga olib keladi).
from app import models  # noqa: F401
from app.config import settings
from app.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    @event.listens_for(connectable, "connect")
    def _disable_sqlite_foreign_keys(dbapi_connection: object, _record: object) -> None:
        """SQLite jadvalni qayta qurish (batch/recreate) paytida ON DELETE CASCADE ishlamasin."""
        if not isinstance(dbapi_connection, sqlite3.Connection):
            return
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=OFF")
        finally:
            cursor.close()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
