import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import os
from pathlib import Path

def _load_env_file():
    for cand in [Path(__file__).resolve().parent.parent / ".env",
                 Path(__file__).resolve().parent.parent / ".env.local",
                 Path(__file__).resolve().parent.parent / ".env.example"]:
        if cand.exists():
            for line in cand.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)

_load_env_file()

import os

from app.base import Base
from app.timekeeping import models
from app.models.core import Tenant, User, TenantSettings
from app.models.crm import Client, Site
from app.models.quoting import Deal, Quote, QuoteParam, QuoteLine, QuoteOverhead, QuoteTotals

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


# --- AUTOGEN FILTER: only timekeeping (tk_*) ---
def include_object(obj, name, type_, reflected, compare_to):
    # autogenerate: bierzemy tylko tabele timekeeping
    if type_ == "table":
        return name.startswith("tk_") or name == "alembic_version"
    return True
# --- /AUTOGEN FILTER ---


def get_url():
    return os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")

def run_migrations_offline():
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    config.set_main_option("sqlalchemy.url", "sqlite:///./app.db")
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
