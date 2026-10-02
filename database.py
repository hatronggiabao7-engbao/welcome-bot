#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite storage cho config welcome/goodbye — bền vững qua restart.
"""
import aiosqlite
import asyncio

DB_PATH = "welcome.db"
_db = None
_lock = asyncio.Lock()


async def get_db() -> aiosqlite.Connection:
    global _db
    async with _lock:
        if _db is None:
            _db = await aiosqlite.connect(DB_PATH)
            _db.row_factory = aiosqlite.Row
            await _init_tables(_db)
        return _db


async def _init_tables(db: aiosqlite.Connection):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id           TEXT PRIMARY KEY,
            welcome_channel    TEXT,
            goodbye_channel    TEXT,
            welcome_title      TEXT,
            welcome_message    TEXT,
            welcome_banner     TEXT,
            welcome_thumbnail  TEXT,
            welcome_footer     TEXT,
            welcome_color      INTEGER,
            welcome_role       TEXT,
            goodbye_title      TEXT,
            goodbye_message    TEXT,
            goodbye_banner     TEXT,
            goodbye_thumbnail  TEXT,
            goodbye_footer     TEXT,
            goodbye_color      INTEGER
        )
    """)
    await db.commit()


async def close_db():
    global _db
    async with _lock:
        if _db is not None:
            await _db.close()
            _db = None


async def get_config(guild_id: str) -> dict:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
    ) as cur:
        row = await cur.fetchone()
        return dict(row) if row else {}


async def set_config(guild_id: str, **kwargs):
    """Upsert config. Chỉ update các field được truyền vào."""
    if not kwargs:
        return
    db = await get_db()
    await db.execute(
        "INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,)
    )
    fields = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [guild_id]
    await db.execute(
        f"UPDATE guild_config SET {fields} WHERE guild_id = ?", values
    )
    await db.commit()


async def unset_config(guild_id: str, *fields):
    """Set các field về NULL."""
    if not fields:
        return
    db = await get_db()
    sets = ", ".join(f"{f} = NULL" for f in fields)
    await db.execute(
        f"UPDATE guild_config SET {sets} WHERE guild_id = ?", (guild_id,)
    )
    await db.commit()