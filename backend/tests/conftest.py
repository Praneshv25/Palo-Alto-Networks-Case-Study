import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import database
from app import create_app


@pytest.fixture()
def app(tmp_path):
    db_path = str(tmp_path / "test.db")
    database.DATABASE = db_path

    app = create_app({"TESTING": True})
    yield app

    database.DATABASE = os.path.join(os.path.dirname(__file__), "..", "guardian.db")


@pytest.fixture()
def client(app):
    return app.test_client()
