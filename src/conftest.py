import os
from collections.abc import Generator
from typing import Any
from unittest.mock import Mock
import pytest
{% if use_api == 'y' %}
from fastapi.testclient import TestClient
{% endif %}

{% if use_db == "y" %}
from hexrepo_db.interface import UOW
{% endif %}
{% if use_db == "y" and use_db_logic == "sql" %}
from app.adaptor.db.sql.uow import SqlUOW
{% elif use_db == "y" and use_db_logic == "nosql" %}
from app.adaptor.db.nosql import DynamoUOW
{% else %}
from app.interactor.dependencies import StubbedUOW
{% endif %}
from hexrepo_db import UOW

from app.domain.example import ExampleDTO

{% if use_db == "y" and use_db_logic == "sql" %}
# Silence SQLALchemy deprecation warning until we can upgrade
os.environ["SQLALCHEMY_SILENCE_UBER_WARNING"] = "1"


def reset_db(uow: UOW, drop_only: bool = False):
    try:
        uow.drop_all()
    except Exception:
        pass
    if not drop_only:
        uow.create_all()


# Create local file db
@pytest.fixture
def SQLALCHEMY_DATABASE_URL():
    return os.getenv(
        "TEST_DB_URL", "postgresql+psycopg://postgres:password@localhost:5432/test_db"
    )


@pytest.fixture
def SQLITE_DATABASE_URL():
    return "sqlite:///test.db"


@pytest.fixture
def uow_lite(SQLITE_DATABASE_URL) -> Generator[UOW, None, None]:
    """
    Return db adaptor with initialised DB & DB session.
    """
    uow = SqlUOW(db_url=SQLITE_DATABASE_URL)
    # Create DB session
    with uow.transaction() as session:  # noqa
        reset_db(uow)
        yield uow


@pytest.fixture
def uow(SQLALCHEMY_DATABASE_URL) -> Generator[UOW, None, None]:
    """
    Return db adaptor with initialised DB & DB session.
    """
    uow = SqlUOW(db_url=SQLALCHEMY_DATABASE_URL)
    # Create DB session
    with uow.transaction() as session:
        reset_db(uow)
        yield uow
{% elif use_db == "y" and use_db_logic == "nosql" %}
@pytest.fixture
def uow() -> Generator[UOW, None, None]:
    """
    Return db adaptor with initialised DB & DB session.
    """
    uow = DynamoUOW(db_url="http://localhost:8888")
    # Create DB session
    yield uow
{% endif %}


{% if use_db == "y" and use_db == "y" %}
@pytest.fixture(scope="function")
def create_tables(uow: UOW):
    reset_db(uow)


@pytest.fixture(scope="function")
def drop_tables(uow: UOW):
    reset_db(uow, drop_only=True)
{% endif %}


{% if use_api == 'y' and use_db == 'n' %}
@pytest.fixture
def uow() -> Generator[UOW, None, None]:
    yield StubbedUOW(db_url="test")
{% endif %}

{% if use_api == "y" %}
@pytest.fixture
def client(uow):
    from app.interactor.api.fastapi import app
    from app.interactor.dependencies import get_uow

    def get_uow_override():
        yield uow

    app.dependency_overrides[get_uow] = get_uow_override
    return TestClient(app)


@pytest.fixture
def example_data():
    return {
        "name": "test",
        "url": "https://test.com",
        "location": "test location",
    }


@pytest.fixture
def created_example(client: TestClient, example_data) -> ExampleDTO:
    response = client.post("/api/v1/example/", json=example_data)
    return ExampleDTO(**response.json())

{% endif %}