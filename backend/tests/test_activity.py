def test_activity_filtering(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "act.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 2, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    client.post(f"/api/v1/uploads/{sid}/complete", json={})

    r = client.get("/api/v1/activity", params={"owner_token": owner})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert any(e["event_type"] == "upload_completed" for e in data["items"])

    r = client.get("/api/v1/activity", params={"owner_token": owner, "event_type": "upload_completed"})
    assert r.status_code == 200
    assert all(e["event_type"] == "upload_completed" for e in r.json()["items"])

    # pagination
    r = client.get("/api/v1/activity", params={"owner_token": owner, "limit": 1, "offset": 0})
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 1


def test_unauthorized_file_access(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "secret.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    fid = r.json()["file_id"]
    # different owner
    r = client.get(f"/api/v1/files/{fid}", params={"owner_token": "other-owner"})
    assert r.status_code == 403


def test_delete_file(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "del.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    fid = r.json()["file_id"]
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 2, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    client.post(f"/api/v1/uploads/{sid}/complete", json={})
    r = client.delete(f"/api/v1/files/{fid}", params={"owner_token": owner})
    assert r.status_code == 200
    r = client.get(f"/api/v1/files/{fid}", params={"owner_token": owner})
    assert r.status_code == 404