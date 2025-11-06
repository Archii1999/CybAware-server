from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool

# --- JOUW imports
from app.core.config import settings          # <--
from app.db import Base                       # <--
from app import models                        # <--

config = context.config

# Logging (optioneel maar handig)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Gebruik dezelfde URL als je app
url = settings.DATABASE_URL
if not url:
    raise RuntimeError("DATABASE_URL is leeg. Zet 'm in .env of in Settings.")
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite tip: batch rendering maakt ALTER TABLE mogelijk
        render_as_batch=True if url.startswith("sqlite") else False,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True if url.startswith("sqlite") else False,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
