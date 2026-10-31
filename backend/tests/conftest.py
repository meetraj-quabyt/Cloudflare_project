import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.db import Database


class FakeStorage:
    def __init__(self):
        self.objects = {}
    def is_local(self):
        return False
    def presign_upload(self, key, session_id="", expires=0):
        return f"http://fake-upload/{key}"
    def presign_download(self, key, file_id="", expires=0):
        return f"http://fake-download/{key}"
    async def head_object(self, key):
        return self.objects.get(key)
    async def delete_object(self, key):
        self.objects.pop(key, None)
        return True


@pytest.fixture
def tmp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except OSError:
        pass


@pytest.fixture
def client(tmp_db_path, monkeypatch):
    monkeypatch.setenv("FRONTEND_BASE_URL", "http://localhost:5173")
    app = create_app()
    # replace db with temp sqlite
    db = Database(sqlite_path=tmp_db_path)
    import asyncio
    asyncio.get_event_loop().run_until_complete(db.connect())
    # apply migration
    mig_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "migrations", "0001_init.sql")
    with open(mig_path) as f:
        asyncio.get_event_loop().run_until_complete(db.executescript(f.read()))
    app.state.db = db
    app.state.storage = FakeStorage()
    # disable lifespan db connect (already connected) by overriding lifespan? TestClient will run lifespan; it will connect again to same path? create_app lifespan uses app.state.db. We replaced it; lifespan will call db.connect (already connected -> aiosqlite connect again? Database.connect checks _conn). It's None initially for new db? We set db and connected, _conn set. lifespan connect sees _conn not None -> skip. close at shutdown closes. Fine.
    with TestClient(app) as c:
        # store fake storage objects accessor
        c.app.state.storage = app.state.storage
        yield c
    asyncio.get_event_loop().run_until_complete(db.close())


@pytest.fixture
def owner():
    return "test-owner-1"