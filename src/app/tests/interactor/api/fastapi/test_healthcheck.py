from fastapi.testclient import TestClient


def test_read_main(client: TestClient):
    response = client.get("/api/v1/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status_message": "OK"}
