"""ZhaomuClient 缓存和 FastAPI DB 依赖。"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, TypeVar

from fastapi import Request

if TYPE_CHECKING:
    import aiosqlite

from zhaomu.client import ZhaomuClient

# 模块级客户端缓存，按 account_id 索引
_client_cache: dict[int, ZhaomuClient] = {}

T = TypeVar("T")


async def get_client(account_id: int, db: "aiosqlite.Connection") -> ZhaomuClient:
    """获取缓存的 ZhaomuClient，不存在时从数据库解密 apikey 后创建。"""
    client = _client_cache.get(account_id)
    if client is not None:
        return client

    rows = list(await db.execute_fetchall(
        "SELECT apikey FROM accounts WHERE id = ?", (account_id,),
    ))
    if not rows:
        raise ValueError(f"账户 {account_id} 不存在")

    from admin.crypto import decrypt_secret
    apikey = decrypt_secret(rows[0]["apikey"])  # pyright: ignore[reportAny]

    _client_cache[account_id] = ZhaomuClient(apikey=apikey)
    return _client_cache[account_id]


def clear_client(account_id: int) -> None:
    """从缓存中移除并关闭指定账户的客户端。"""
    client = _client_cache.pop(account_id, None)
    if client is not None:
        client.close()


async def get_db(request: Request) -> AsyncGenerator["aiosqlite.Connection", None]:
    """FastAPI 依赖注入：从 app.state.admin_db_path 读取数据库路径，请求结束时关闭连接。

    表创建 SQL 从 admin.db 模块导入，避免重复定义。
    """
    import aiosqlite
    from admin.db import _CREATE_ACCOUNTS, _CREATE_SETTINGS, _CREATE_SERVERS

    db_path: str = request.app.state.admin_db_path  # pyright: ignore[reportAny]
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    _ = await conn.execute("PRAGMA foreign_keys = ON")
    _ = await conn.execute(_CREATE_ACCOUNTS)
    _ = await conn.execute(_CREATE_SETTINGS)
    _ = await conn.execute(_CREATE_SERVERS)
    await conn.commit()
    try:
        yield conn
    finally:
        await conn.close()


async def run_async(func: Any, *args: Any, **kwargs: Any) -> Any:
    """在默认线程池中执行同步函数，避免阻塞 FastAPI 事件循环。"""
    return await asyncio.to_thread(func, *args, **kwargs)
