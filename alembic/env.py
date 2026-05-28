"""
alembic/env.py — Alembic Migration Configuration
--------------------------------------------------
Alembic migration tool ka config file.

Kya karta hai:
1. App ke models import karta hai
2. Database URL .env se load karta hai
3. Migrations run karne ka logic

COMMANDS:
  alembic revision --autogenerate -m "Initial tables"  ← migration file banao
  alembic upgrade head                                  ← migrations apply karo
  alembic downgrade -1                                  ← ek step peeche jao
  alembic history                                       ← history dekho

Requirement #5 fulfill ho raha hai — Alembic migrations
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# App ka path add karo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Sabhi models import karo — Alembic inhe detect karega
from app.database import Base
from app.models import User, Complaint, Assignment, AuditLog  # noqa
from app.config import settings

# Alembic config object
config = context.config

# .env se DATABASE_URL lo
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata — Alembic yahi compare karega tables ke liye
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline mode — bina actual DB connection ke SQL generate karo"""
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
    """Online mode — actual DB se connect karke migrations run karo"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,    # Column type changes detect karo
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
