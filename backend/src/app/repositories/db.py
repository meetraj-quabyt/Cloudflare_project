from typing import Any

try:
    import aiosqlite  # type: ignore
except Exception:  # noqa: BLE001
    aiosqlite = None  # type: ignore


class Database:
    """Async database adapter. Supports aiosqlite (local) and Cloudflare D1 binding."""

    def __init__(self, sqlite_path: str | None = None, d1_binding: Any = None):
        self.sqlite_path = sqlite_path
        self.d1 = d1_binding
        self._conn: Any = None

    @property
    def is_d1(self) -> bool:
        return self.d1 is not None

    async def connect(self) -> None:
        if self.is_d1:
            return
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.sqlite_path or ":memory:")  # type: ignore[union-attr]
            self._conn.row_factory = aiosqlite.Row  # type: ignore[union-attr]
            await self._conn.execute("PRAGMA foreign_keys = ON")  # type: ignore[union-attr]

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def execute(self, sql: str, params: tuple | list = ()) -> None:
        if self.is_d1:
            stmt = self.d1.prepare(sql)
            if params:
                stmt = stmt.bind(*list(params))
            await stmt.run()
            return
        await self.connect()
        assert self._conn is not None
        await self._conn.execute(sql, tuple(params))
        await self._conn.commit()

    async def fetch_one(self, sql: str, params: tuple | list = ()) -> dict | None:
        if self.is_d1:
            stmt = self.d1.prepare(sql)
            if params:
                stmt = stmt.bind(*list(params))
            row = await stmt.first()
            if row is None:
                return None
            # row may be a dict-like or a list
            try:
                return dict(row)
            except Exception:  # noqa: BLE001
                # FFI object: convert via keys? fallback
                return row if isinstance(row, dict) else None
        await self.connect()
        assert self._conn is not None
        cur = await self._conn.execute(sql, tuple(params))
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        return dict(row)

    async def fetch_all(self, sql: str, params: tuple | list = ()) -> list[dict]:
        if self.is_d1:
            stmt = self.d1.prepare(sql)
            if params:
                stmt = stmt.bind(*list(params))
            res = await stmt.all()
            rows = getattr(res, "results", None)
            if rows is None and isinstance(res, dict):
                rows = res.get("results", [])
            if rows is None:
                rows = res
            out = []
            for r in rows or []:
                try:
                    out.append(dict(r))
                except Exception:  # noqa: BLE001
                    out.append(r if isinstance(r, dict) else {})
            return out
        await self.connect()
        assert self._conn is not None
        cur = await self._conn.execute(sql, tuple(params))
        rows = await cur.fetchall()
        await cur.close()
        return [dict(r) for r in rows]

    async def executescript(self, script: str) -> None:
        if self.is_d1:
            # D1 doesn't support executescript via binding easily; split statements
            for stmt in script.split(";"):
                s = stmt.strip()
                if s:
                    await self.execute(s + ";")
            return
        await self.connect()
        assert self._conn is not None
        await self._conn.executescript(script)
        await self._conn.commit()


def row_to_dict(row) -> dict:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:  # noqa: BLE001
        return {}