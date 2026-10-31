"""
D1 REST API database adapter for use inside Cloudflare Containers.

When the backend runs as a container (not a Python Worker) it has no access to
env.DB (the D1 binding).  Instead this adapter calls the Cloudflare D1 REST API
directly using credentials supplied via environment variables:

    CLOUDFLARE_ACCOUNT_ID  – Cloudflare account ID
    CF_D1_DATABASE_ID      – D1 database UUID
    CLOUDFLARE_D1_TOKEN    – API token with D1 edit permission

The class exposes the same async interface as ``app.repositories.db.Database``
so the rest of the application is unaware of the difference.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


class D1RestDatabase:
    """Async D1 database adapter that communicates over the REST API."""

    def __init__(self) -> None:
        self._account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        self._database_id = os.environ.get("CF_D1_DATABASE_ID", "")
        self._token = os.environ.get("CLOUDFLARE_D1_TOKEN", "")
        self._base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self._account_id}/d1/database/{self._database_id}/query"
        )

    # ------------------------------------------------------------------
    # Lifecycle (no-ops for the REST adapter)
    # ------------------------------------------------------------------

    async def connect(self) -> None:  # noqa: D401
        """No-op: REST adapter needs no persistent connection."""

    async def close(self) -> None:  # noqa: D401
        """No-op: REST adapter needs no persistent connection."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def is_d1(self) -> bool:
        return True

    async def execute(self, sql: str, params: tuple | list = ()) -> None:
        """Execute a write statement (INSERT / UPDATE / DELETE / DDL)."""
        await self._query(sql, list(params))

    async def fetch_one(self, sql: str, params: tuple | list = ()) -> dict | None:
        """Return the first row as a dict, or None if the result set is empty."""
        rows = await self._query(sql, list(params))
        return rows[0] if rows else None

    async def fetch_all(self, sql: str, params: tuple | list = ()) -> list[dict]:
        """Return all rows as a list of dicts."""
        return await self._query(sql, list(params))

    async def executescript(self, script: str) -> None:
        """Execute multiple semicolon-separated SQL statements sequentially."""
        for statement in script.split(";"):
            stripped = statement.strip()
            if stripped:
                await self.execute(stripped + ";")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _query(self, sql: str, params: list[Any]) -> list[dict]:
        """POST a SQL query to the D1 REST endpoint and return result rows."""
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"sql": sql}
        if params:
            payload["params"] = params

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(self._base_url, json=payload, headers=headers)

        response.raise_for_status()
        data: dict[str, Any] = response.json()

        if not data.get("success"):
            errors = data.get("errors", [])
            raise RuntimeError(f"D1 REST API error: {errors}")

        # Response shape: {"result": [{"results": [...], "success": true}], "success": true}
        result_list = data.get("result", [])
        if not result_list:
            return []

        first_result = result_list[0]
        rows: list[Any] = first_result.get("results", []) or []
        return [dict(row) for row in rows]
