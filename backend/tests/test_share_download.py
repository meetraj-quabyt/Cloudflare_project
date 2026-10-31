def test_share_and_download_flow(client, owner):
    # upload first
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "share.txt", "content_type": "text/plain", "size_bytes": 4, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    r.json()["file_id"]
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 4, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 200
    token = r.json()["share_token"]

    # public share info
    r = client.get(f"/api/v1/shares/{token}")
    assert r.status_code == 200
    assert r.json()["file_name"] == "share.txt"

    # invalid token
    r = client.get("/api/v1/shares/notavalidtoken")
    assert r.status_code == 404

    # initiate download
    r = client.post(f"/api/v1/shares/{token}/downloads")
    assert r.status_code == 200, r.text
    dl = r.json()
    dlsid = dl["download_session_id"]
    assert "download_url" in dl

    # complete download (client reported)
    r = client.post(f"/api/v1/downloads/{dlsid}/complete", json={"bytes_transferred": 4})
    assert r.status_code == 200
    assert r.json()["status"] == "client_reported_complete"

    # idempotent
    r = client.post(f"/api/v1/downloads/{dlsid}/complete", json={"bytes_transferred": 4})
    assert r.status_code == 200
    assert r.json().get("idempotent") is True

    # fail another session
    r = client.post(f"/api/v1/shares/{token}/downloads")
    assert r.status_code == 200
    dlsid2 = r.json()["download_session_id"]
    r = client.post(f"/api/v1/downloads/{dlsid2}/fail", json={"reason": "network"})
    assert r.status_code == 200
    assert r.json()["status"] == "failed"


def test_revoked_link(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "rev.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 2, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    token = r.json()["share_token"]
    share_id = r.json()["share_id"]

    # revoke
    r = client.post(f"/api/v1/shares/{share_id}/revoke", headers={"X-CloudShare-Owner": owner})
    assert r.status_code == 200

    # public info now revoked
    r = client.get(f"/api/v1/shares/{token}")
    assert r.status_code == 410

    # download rejected
    r = client.post(f"/api/v1/shares/{token}/downloads")
    assert r.status_code == 410


def test_download_limit(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "lim.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 2, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    # create share with max_downloads=1 via create_share? Already created in complete without limit. Use files share endpoint to rotate with limit
    fid = r.json()["file_id"]
    r = client.post(f"/api/v1/files/{fid}/share", json={"max_downloads": 1, "owner_token": owner})
    assert r.status_code == 200
    token = r.json()["share_url"].split("/")[-1]

    # first download ok
    r = client.post(f"/api/v1/shares/{token}/downloads")
    assert r.status_code == 200

    # second rejected (count still 0 but max 1; initiated doesn't increment count; so second also ok by count). 
    # To enforce, complete first to increment count
    # Actually count increments on completion. Let's complete first then second should be rejected.
    r.json()["download_session_id"] if r.status_code == 200 else None
    # re-init since previous consumed? Let's just test count-based: complete first download
    # We need a fresh download session
    r = client.post(f"/api/v1/shares/{token}/downloads")
    # This may succeed because count 0. Complete it.
    if r.status_code == 200:
        ds = r.json()["download_session_id"]
        client.post(f"/api/v1/downloads/{ds}/complete", json={"bytes_transferred": 2})
    # now count=1, next should be rejected
    r = client.post(f"/api/v1/shares/{token}/downloads")
    assert r.status_code == 429


def test_expired_session(client, owner):
    r = client.post("/api/v1/uploads/initiate", json={
        "filename": "exp.txt", "content_type": "text/plain", "size_bytes": 2, "owner_token": owner,
    })
    sid = r.json()["session_id"]
    # manually expire
    db = client.app.state.db
    import asyncio
    asyncio.get_event_loop().run_until_complete(db.execute("UPDATE upload_sessions SET expires_at = '2000-01-01T00:00:00+00:00' WHERE id = ?", (sid,)))
    r2 = client.app.state.storage
    async def head_ok(key):
        return {"size": 2, "content_type": "text/plain", "etag": "x"}
    r2.head_object = head_ok
    r = client.post(f"/api/v1/uploads/{sid}/complete", json={})
    assert r.status_code == 410