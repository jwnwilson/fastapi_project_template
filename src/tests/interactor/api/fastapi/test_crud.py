from datetime import datetime
from unittest.mock import Mock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexrepo_api.crud import CrudRouter
from hexrepo_db.exception import RecordNotFound
from hexrepo_db.interface import PaginatedData
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel


class MockCreateSchema(BaseModel):
    name: str


class MockUpdateSchema(BaseModel):
    name: str


class MockResponseSchema(BaseModel):
    id: UUID
    name: str
    created_at: datetime


class MockResponseFactory(ModelFactory):
    __model__ = MockResponseSchema


mock_responses = MockResponseFactory.batch(3)


class MockRepository:
    def __init__(self):
        self.data = mock_responses

    def create(self, obj_in):
        return MockResponseSchema(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            name=obj_in.name,
            created_at=datetime.strptime(
                "2024-08-30T08:06:10.591198", "%Y-%m-%dT%H:%M:%S.%f"
            ),
        )

    def read(self, id: UUID):
        if id == UUID("00000000-0000-0000-0000-000000000000"):
            raise RecordNotFound("Record not found")
        return MockResponseSchema(
            id=id,
            name="test",
            created_at=datetime.strptime(
                "2024-08-30T08:06:10.591198", "%Y-%m-%dT%H:%M:%S.%f"
            ),
        )

    def read_multi(
        self,
        filters,
        page_size=100,
        page_number=1,
        order_by="-created_at",
    ):
        results = sorted(
            self.data,
            key=lambda x: getattr(x, order_by.lstrip("-")),
            reverse=(order_by.startswith("-")),
        )
        start = (page_number - 1) * page_size
        end = start + page_size
        return PaginatedData(results=results, total=len(self.data))

    def update(self, id: UUID, obj_in):
        return MockResponseSchema(
            id=id,
            name=obj_in.name,
            created_at=datetime.strptime(
                "2024-08-30T08:06:10.591198", "%Y-%m-%dT%H:%M:%S.%f"
            ),
        )

    def delete(self, id: UUID):
        if id == UUID("00000000-0000-0000-0000-000000000000"):
            raise RecordNotFound("Record not found")
        return


class MockUOW:
    repository = MockRepository()

    @property
    def session(self):
        return Mock()


@pytest.fixture
def client():
    def get_repos():
        return MockUOW()

    router = CrudRouter(
        db_dependency=get_repos,
        repository="repository",
        response_schema=MockResponseSchema,
        methods=["CREATE", "READ", "UPDATE", "DELETE"],
        create_schema=MockCreateSchema,
        update_schema=MockUpdateSchema,
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_initialization():
    def get_repos():
        return MockUOW()

    router = CrudRouter(
        db_dependency=get_repos,
        repository="repository",
        response_schema=MockResponseSchema,
        methods=["CREATE", "READ", "UPDATE", "DELETE"],
        create_schema=MockCreateSchema,
        update_schema=MockUpdateSchema,
    )
    assert router.db_dependency == get_repos
    assert router.repository == "repository"
    assert router.response_schema == MockResponseSchema
    assert router.create_schema == MockCreateSchema
    assert router.update_schema == MockUpdateSchema


def test_create_route(client: TestClient):
    response = client.post("/", json={"name": "test"})
    assert response.status_code == 200
    assert response.json() == {
        "id": "12345678-1234-5678-1234-567812345678",
        "name": "test",
        "created_at": "2024-08-30T08:06:10.591198",
    }


def test_read_route(client: TestClient):
    response = client.get("/12345678-1234-5678-1234-567812345678")
    assert response.status_code == 200
    assert response.json() == {
        "id": "12345678-1234-5678-1234-567812345678",
        "name": "test",
        "created_at": "2024-08-30T08:06:10.591198",
    }


def test_read_route_not_found_exc(client: TestClient):
    # with pytest.raises(RecordNotFound):
    response = client.get("/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_route(client: TestClient):
    response = client.patch(
        "/12345678-1234-5678-1234-567812345678", json={"name": "updated"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": "12345678-1234-5678-1234-567812345678",
        "name": "updated",
        "created_at": "2024-08-30T08:06:10.591198",
    }


def test_delete_route(client: TestClient):
    response = client.delete("/12345678-1234-5678-1234-567812345678")
    assert response.status_code == 204

    response = client.delete("/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_read_multi_route_with_ordering_asc(client: TestClient):
    response = client.get("/?order_by=name")
    assert response.status_code == 200
    data = response.json()
    results = [MockResponseSchema(**d) for d in data["results"]]
    assert results == sorted(mock_responses, key=lambda m: m.name)


def test_read_multi_route_with_ordering_desc(client: TestClient):
    response = client.get("/?order_by=-name")
    assert response.status_code == 200
    data = response.json()
    results = [MockResponseSchema(**d) for d in data["results"]]
    assert results == sorted(mock_responses, key=lambda m: m.name, reverse=True)
