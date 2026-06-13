import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("JWT_SECRET", "test-secret-with-enough-length")
    monkeypatch.setenv("ENABLE_PUBLIC_TECH_REGISTRATION", "false")

    database = importlib.import_module("database")
    database.DB_PATH = str(tmp_path / "pato-test.db")

    main = importlib.import_module("main")
    main.db.DB_PATH = database.DB_PATH
    main.db.init_db()
    main.seed_demo()

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture()
def login_as(client: TestClient):
    def _login(email: str, password: str = "1234") -> str:
        response = client.post("/api/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()["token"]

    return _login
