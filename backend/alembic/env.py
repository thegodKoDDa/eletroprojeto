import os

from alembic import context
from app.database import DEFAULT_DATABASE_URL, Base
from sqlalchemy import engine_from_config, pool

config = context.config
config.set_main_option(
    "sqlalchemy.url", os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).replace("%", "%%")
)
if context.is_offline_mode():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=Base.metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
