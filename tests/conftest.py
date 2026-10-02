import os
import tempfile

import pytest

import mcp_agent_router.db as db


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch):
    """Each test gets its own SQLite file so seed data and writes don't leak across tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        monkeypatch.setattr(db, "DB_PATH", os.path.join(tmp_dir, "test.db"))
        yield
