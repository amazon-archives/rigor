from __future__ import with_statement
from alembic import context
from sqlalchemy import create_engine, pool, MetaData
from logging.config import fileConfig
import rigor.database
from rigor.config import RigorDefaultConfiguration

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# The configuration supplied by Rigor
rigor_config = RigorDefaultConfiguration()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = MetaData(naming_convention=rigor.database.kNamingConvention)

# other values from the config, defined by the needs of env.py,
# can be acquired:
#database = config.get_main_option("database")
database = raw_input('Database name: ')
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = rigor.database.Database.build_url('', rigor_config)
    context.configure(url=url, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = rigor.database.Database.build_url(database, rigor_config)
    engine = create_engine(url, poolclass=pool.NullPool)

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
