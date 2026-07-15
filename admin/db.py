"""admin/db.py — SQLite 持久层，使用 aiosqlite 实现异步 CRUD。

提供 accounts / settings / servers 三张表及其增删改查操作。
所有 CRUD 函数均以 aiosqlite.Connection 作为第一个参数，
由调用方通过 get_db() 上下文管理器获取连接。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import aiosqlite
from aiosqlite import Row


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------


@dataclass
class AccountRecord:
    """帐户记录。"""
    id: int
    name: str
    apikey: str
    created_at: str = ""


@dataclass
class ServerRecord:
    """云服务器记录 — 镜像 servers 表的所有列。"""
    id: int
    account_id: int
    server_id: int
    product_id: int
    region_id: int
    image: str = ""
    disk: int = 0
    payment_cycle: int = 0
    ip: str = ""
    status: str = "provisioning"
    deployed_at: str = ""
    ordered_at: str = ""
    destroyed_at: str = ""
    has_refund: int = 0


# ---------------------------------------------------------------------------
# 建表 SQL（首次连接时自动执行）
# ---------------------------------------------------------------------------

_CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    apikey TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""

_CREATE_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

_CREATE_SERVERS = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    server_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    region_id INTEGER NOT NULL,
    image TEXT,
    disk INTEGER,
    payment_cycle INTEGER,
    ip TEXT,
    status TEXT DEFAULT 'provisioning',
    deployed_at TEXT,
    ordered_at TEXT DEFAULT CURRENT_TIMESTAMP,
    destroyed_at TEXT,
    has_refund INTEGER DEFAULT 0
)
"""


# ---------------------------------------------------------------------------
# 数据库连接上下文管理器
# ---------------------------------------------------------------------------


@asynccontextmanager
async def get_db(
    db_path: str = "admin.db",
) -> AsyncGenerator[aiosqlite.Connection, None]:
    """获取 SQLite 数据库连接，首次使用时自动创建表。

    用法::

        async with get_db("path/to/admin.db") as db:
            accounts = await list_accounts(db)

    参数:
        db_path: 数据库文件路径，默认为当前工作目录下的 admin.db。
    """
    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    # 启用外键约束（SQLite 默认不检查外键）
    _ = await conn.execute("PRAGMA foreign_keys = ON")
    # 首次使用时创建表（IF NOT EXISTS 保证幂等）
    _ = await conn.execute(_CREATE_ACCOUNTS)
    _ = await conn.execute(_CREATE_SETTINGS)
    _ = await conn.execute(_CREATE_SERVERS)
    await conn.commit()
    try:
        yield conn
    finally:
        await conn.close()


# ---------------------------------------------------------------------------
# Account — 帐户增删查
# ---------------------------------------------------------------------------


async def create_account(
    db: aiosqlite.Connection, name: str, apikey: str,
) -> AccountRecord:
    """创建帐户，返回包含 id 和 created_at 的完整记录。"""
    cursor = await db.execute(
        "INSERT INTO accounts (name, apikey) VALUES (?, ?)",
        (name, apikey),
    )
    await db.commit()
    rows = list(await db.execute_fetchall(
        "SELECT id, name, apikey, created_at FROM accounts WHERE id = ?",
        (cursor.lastrowid,),
    ))
    return _row_to_account(rows[0])


async def list_accounts(db: aiosqlite.Connection) -> list[AccountRecord]:
    """列出所有帐户，按 id 升序排列。"""
    rows = list(await db.execute_fetchall(
        "SELECT id, name, apikey, created_at FROM accounts ORDER BY id",
    ))
    return [_row_to_account(r) for r in rows]


async def delete_account(db: aiosqlite.Connection, account_id: int) -> None:
    """删除帐户，ON DELETE CASCADE 会自动删除关联的服务器记录。"""
    _ = await db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    await db.commit()


# ---------------------------------------------------------------------------
# Settings — 键值配置
# ---------------------------------------------------------------------------


async def get_setting(db: aiosqlite.Connection, key: str) -> str | None:
    """读取设置项的值，key 不存在时返回 None。"""
    rows = list(await db.execute_fetchall(
        "SELECT value FROM settings WHERE key = ?", (key,),
    ))
    if not rows:
        return None
    return rows[0]["value"]  # pyright: ignore[reportAny]


async def set_setting(db: aiosqlite.Connection, key: str, value: str) -> None:
    """写入设置项（INSERT OR REPLACE — 新建或覆盖已有 key）。"""
    _ = await db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Server — 云服务器记录增改查
# ---------------------------------------------------------------------------


async def create_server_record(
    db: aiosqlite.Connection,
    account_id: int,
    server_id: int,
    product_id: int,
    region_id: int,
    *,
    image: str = "",
    disk: int = 0,
    payment_cycle: int = 1,
    ip: str = "",
    status: str = "provisioning",
) -> ServerRecord:
    """创建一条云服务器记录，返回包含所有字段的完整记录。"""
    cursor = await db.execute(
        """INSERT INTO servers
           (account_id, server_id, product_id, region_id,
            image, disk, payment_cycle, ip, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (account_id, server_id, product_id, region_id,
         image, disk, payment_cycle, ip, status),
    )
    await db.commit()
    rows = list(await db.execute_fetchall(
        "SELECT * FROM servers WHERE id = ?", (cursor.lastrowid,),
    ))
    return _row_to_server(rows[0])


async def update_server_status(
    db: aiosqlite.Connection, server_db_id: int, status: str,
    *, ip: str = "", deployed_at: str = "", destroyed_at: str = "",
) -> None:
    """更新服务器状态，可选地同时更新 IP / 部署时间 / 销毁时间。

    ip / deployed_at / destroyed_at 传空字符串表示不修改该字段。
    """
    _ = await db.execute(
        """UPDATE servers
           SET status = ?,
               ip = CASE WHEN ? != '' THEN ? ELSE ip END,
               deployed_at = CASE WHEN ? != '' THEN ? ELSE deployed_at END,
               destroyed_at = CASE WHEN ? != '' THEN ? ELSE destroyed_at END
           WHERE id = ?""",
        (status,
         ip, ip,
         deployed_at, deployed_at,
         destroyed_at, destroyed_at,
         server_db_id),
    )
    await db.commit()


async def list_servers_by_account(
    db: aiosqlite.Connection, account_id: int,
) -> list[ServerRecord]:
    """列出指定帐户下的所有服务器记录，按 id 升序排列。"""
    rows = list(await db.execute_fetchall(
        "SELECT * FROM servers WHERE account_id = ? ORDER BY id",
        (account_id,),
    ))
    return [_row_to_server(r) for r in rows]


async def get_server_record(
    db: aiosqlite.Connection, server_db_id: int,
) -> ServerRecord | None:
    """按内部 ID 查询服务器记录，不存在时返回 None。"""
    rows = list(await db.execute_fetchall(
        "SELECT * FROM servers WHERE id = ?", (server_db_id,),
    ))
    if not rows:
        return None
    return _row_to_server(rows[0])


# ---------------------------------------------------------------------------
# 内部辅助 — aiosqlite.Row → dataclass
# ---------------------------------------------------------------------------


def _row_to_account(row: Row) -> AccountRecord:
    """将 Row 转为 AccountRecord。"""
    return AccountRecord(
        id=row["id"],            # pyright: ignore[reportAny]
        name=row["name"],        # pyright: ignore[reportAny]
        apikey=row["apikey"],    # pyright: ignore[reportAny]
        created_at=row["created_at"],  # pyright: ignore[reportAny]
    )


def _row_to_server(row: Row) -> ServerRecord:
    """将 Row 转为 ServerRecord（NULL 字段以默认值填充）。"""
    return ServerRecord(
        id=row["id"],                        # pyright: ignore[reportAny]
        account_id=row["account_id"],        # pyright: ignore[reportAny]
        server_id=row["server_id"],          # pyright: ignore[reportAny]
        product_id=row["product_id"],        # pyright: ignore[reportAny]
        region_id=row["region_id"],          # pyright: ignore[reportAny]
        image=row["image"] or "",            # pyright: ignore[reportAny]
        disk=row["disk"] or 0,               # pyright: ignore[reportAny]
        payment_cycle=row["payment_cycle"] or 0,  # pyright: ignore[reportAny]
        ip=row["ip"] or "",                  # pyright: ignore[reportAny]
        status=row["status"] or "provisioning",  # pyright: ignore[reportAny]
        deployed_at=row["deployed_at"] or "",    # pyright: ignore[reportAny]
        ordered_at=row["ordered_at"] or "",      # pyright: ignore[reportAny]
        destroyed_at=row["destroyed_at"] or "",  # pyright: ignore[reportAny]
        has_refund=row["has_refund"] or 0,       # pyright: ignore[reportAny]
    )
