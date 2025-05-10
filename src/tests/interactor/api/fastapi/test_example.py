from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def example_data_missing_url():
    return {"name": "test"}


def test_example_create(client: TestClient, example_data):
    response = client.post("/api/v1/example/", json=example_data)
    assert response.status_code == 200
    {% if use_db %}
    assert response.json()["name"] == example_data["name"]
    assert response.json()["url"] == example_data["url"]
    {% endif %}


def test_example_create_missing_url(client: TestClient, example_data_missing_url):
    response = client.post(url="/api/v1/example/", data=example_data_missing_url)
    assert response.status_code == 422


def test_example_read(client: TestClient, created_example):
    example_id = created_example.id
    response = client.get(f"/api/v1/example/{example_id}")
    assert response.status_code == 200
    assert response.json()["name"] == created_example.name
    assert response.json()["url"] == created_example.url


{% if use_db and use_db_logic == "sql" %}
def test_example_read_filter_name(client: TestClient, created_example):
    response = client.get(
        f'/api/v1/example/?filters=%7B"name"%3A"{created_example.name}"%7D'
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_example_read_filter_none(client: TestClient, created_example):
    response = client.get(f'/api/v1/example/?filters=%7B"name"%3A"doesntexist"%7D')
    assert response.status_code == 200
    assert response.json()["total"] == 0
{% endif %}


def test_example_update(client: TestClient, created_example):
    company_id = created_example.id
    updated_data = {"url": "test2.com"}
    response = client.patch(f"/api/v1/example/{company_id}", json=updated_data)
    assert response.status_code == 200
    {% if use_db %}
    assert response.json()["url"] == updated_data["url"]

    # Verify the update
    response = client.get(f"/api/v1/example/{company_id}")
    assert response.status_code == 200
    assert response.json()["url"] == updated_data["url"]
    {% endif %}


def test_example_delete(client: TestClient, created_example):
    company_id = created_example.id
    response = client.delete(f"/api/v1/example/{company_id}")
    assert response.status_code == 204

    {% if use_db %}
    # Verify the delete
    response = client.get(f"/api/v1/example/{company_id}")
    assert response.status_code == 404
    {% endif %}
