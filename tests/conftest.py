import os
import tempfile

# Point the app at a throwaway database before models.py creates its engine.
_db_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_db_dir, 'test.db')}"

import pytest
from fastapi.testclient import TestClient

from main import app
from models import Base, engine


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def category(client):
    return client.post("/categories", json={"name": "work"}).json()
