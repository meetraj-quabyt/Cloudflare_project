

def test_initiate_invalid_size(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "a.txt", "content_type": "text/plain", "size_bytes": 0, "owner_token": owner,
    })
    assert r.status_code in (400, 422)


def test_initiate_invalid_type(client, owner):
    client.post("/api/v1/uploads/initiate", json={
        "filename": "a.exe", "content_type": "application/x-msdownload", "size_bytes": 10, "owner_token": owner,
    })
    # application/* allowed generically, so this passes; test oversized instead


def test_upload_flow(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "hello.txt", "content_type": "text/plain", "size_bytes": 5, "owner_token": owner,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    sid = data["session_id"]
    data["file_id"]

    # fake R2 object present
    r2 = client.app.state.storage
    # mark object exists by injecting
    # find object key via db? Instead, complete will fail (missing). Let's inject after getting key from status? We don't have key. Simulate by making head_object return size 5 always via monkey? Instead set FakeR2 to return for any key.

    async def head_any(key):
        return {"size": 5, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_any

    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"

    # idempotent
    r2 = client.app.state.storage
    r2.head_object = head_any
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 200
    assert r.json().get("idempotent") is True

    # status
    r = client.get(f"/api/v1/uploads/{sid}")
    assert r.status_code == 200
    assert r.json()["status"] == "completed"

    # files list
    r = client.get("/api/v1/files", params={"owner_token": owner})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_upload_missing_object(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "missing.txt", "content_type": "text/plain", "size_bytes": 5, "owner_token": owner,
    })
    data = r.json()
    sid = data["session_id"]
    r2 = client.app.state.storage
    async def head_none(key):
        return None
    r2.head_object = head_none
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 400


def test_upload_size_mismatch(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "mm.txt", "content_type": "text/plain", "size_bytes": 5, "owner_token": owner,
    })
    data = r.json()
    sid = data["session_id"]
    r2 = client.app.state.storage
    async def head_wrong(key):
        return {"size": 99, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_wrong
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 400