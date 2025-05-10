import pytest
from pytest_alembic.config import Config

{% if use_db and use_db_logic == "sql" %}
from app.adaptor.db.sql import SqlUOW


@pytest.fixture
def alembic_config(SQLALCHEMY_DATABASE_URL):
    """Override this fixture to configure the exact alembic context setup required."""
    return Config.from_raw_config({"sqlalchemy.url": str(SQLALCHEMY_DATABASE_URL)})


@pytest.fixture
def alembic_engine(uow: SqlUOW, drop_tables):
    """Override this fixture to provide pytest-alembic powered tests with a database handle."""
    return uow.session.get_bind()

{% endif %}