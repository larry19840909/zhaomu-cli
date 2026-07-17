"""admin/tests/test_db.py — admin/db.py 的场景测试。

使用 tmp_path 创建临时数据库文件，asyncio.run() 包装异步操作。
"""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, TypeVar

from admin.db import (
    AccountRecord,
    ServerRecord,
    create_account,
    create_server_record,
    delete_account,
    get_db,
    get_server_record,
    get_setting,
    list_accounts,
    list_servers_by_account,
    migrate_db,
    set_setting,
    update_server_status,
)


# ---------------------------------------------------------------------------
# 辅助 — 将异步函数包装为同步，简化测试写法
# ---------------------------------------------------------------------------


T = TypeVar("T")

def _run(coro: Coroutine[Any, Any, T]) -> T:
    """在当前事件循环中运行协程。"""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 场景 1：创建帐户 + 列出帐户
# ---------------------------------------------------------------------------


class TestAccountCRUD:
    """帐户增删查。"""

    def test_create_and_list_account(self, tmp_path: Path):
        """创建两个帐户后列出，校验名称和记录数量。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                a1 = await create_account(db, "alice", "key-aaaa")
                a2 = await create_account(db, "bob", "key-bbbb")
                all_accounts = await list_accounts(db)

            assert len(all_accounts) == 2
            assert all_accounts[0].name == "alice"
            assert all_accounts[0].apikey == "key-aaaa"
            assert all_accounts[0].id == 1
            assert all_accounts[1].name == "bob"
            assert all_accounts[1].apikey == "key-bbbb"
            assert all_accounts[1].id == 2
            # created_at 由 SQLite 自动填充
            assert all_accounts[0].created_at != ""
            assert all_accounts[1].created_at != ""
            # 验证返回的是 AccountRecord
            assert isinstance(a1, AccountRecord)
            assert isinstance(a2, AccountRecord)

        _run(_test())


# ---------------------------------------------------------------------------
# 场景 2：创建服务器记录 → 更新状态 → 查询
# ---------------------------------------------------------------------------


class TestServerLifecycle:
    """服务器记录生命周期：创建 → 更新 → 查询。"""

    def test_create_update_query_server(self, tmp_path: Path):
        """创建服务器、更新状态为 running、再次查询校验。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                # 先创建帐户（外键依赖）
                await create_account(db, "alice", "key-aaaa")

                # 创建服务器记录
                srv = await create_server_record(
                    db,
                    account_id=1,
                    server_id=280722,
                    product_id=9723,
                    region_id=780,
                    image="Ubuntu 20.04",
                    disk=40,
                    payment_cycle=1,
                    ip="31.210.52.36",
                    status="provisioning",
                )
                assert srv.status == "provisioning"
                assert srv.server_id == 280722
                assert srv.ip == "31.210.52.36"
                assert isinstance(srv, ServerRecord)

                record_id = srv.id

                # 更新状态为 running + 模拟部署完成
                await update_server_status(
                    db, record_id, "running",
                    deployed_at="2025-01-15 10:30:00",
                )

                # 重新查询校验
                updated = await get_server_record(db, record_id)
                assert updated is not None
                assert updated.status == "running"
                assert updated.deployed_at == "2025-01-15 10:30:00"
                # ip 未传（空字符串），应保持不变
                assert updated.ip == "31.210.52.36"

                # 按帐户列出
                servers = await list_servers_by_account(db, 1)
                assert len(servers) == 1
                assert servers[0].status == "running"

            # 查询不存在的记录 → None
            async with get_db(db_path) as db:
                not_found = await get_server_record(db, 999)
                assert not_found is None

        _run(_test())


# ---------------------------------------------------------------------------
# 场景 3：get_setting 对不存在的 key 返回 None
# ---------------------------------------------------------------------------


class TestSettings:
    """键值配置读写。"""

    def test_get_nonexistent_setting_returns_none(self, tmp_path: Path):
        """从未写入的 key 应返回 None。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                assert await get_setting(db, "no_such_key") is None

                # 写入后可以读到
                await set_setting(db, "theme", "dark")
                assert await get_setting(db, "theme") == "dark"

                # 覆盖写入
                await set_setting(db, "theme", "light")
                assert await get_setting(db, "theme") == "light"

                # 不存在的 key 仍为 None
                assert await get_setting(db, "other") is None

        _run(_test())


# ---------------------------------------------------------------------------
# 场景 4：delete_account 级联删除 servers
# ---------------------------------------------------------------------------


class TestCascadeDelete:
    """删除帐户时级联删除关联服务器。"""

    def test_delete_account_cascades_servers(self, tmp_path: Path):
        """删除有 2 台服务器的帐户后，服务器列表为空。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                await create_account(db, "alice", "key-aaaa")
                await create_account(db, "bob", "key-bbbb")

                # alice 有 2 台服务器，bob 有 1 台
                await create_server_record(
                    db, account_id=1, server_id=100, product_id=1, region_id=1,
                )
                await create_server_record(
                    db, account_id=1, server_id=101, product_id=1, region_id=1,
                )
                await create_server_record(
                    db, account_id=2, server_id=200, product_id=1, region_id=1,
                )

                # 验证服务器数量
                assert len(await list_servers_by_account(db, 1)) == 2
                assert len(await list_servers_by_account(db, 2)) == 1

                # 删除 alice
                await delete_account(db, 1)

                # alice 的服务器被级联删除
                assert len(await list_servers_by_account(db, 1)) == 0
                # bob 的服务器不受影响
                assert len(await list_servers_by_account(db, 2)) == 1

                # alice 本身的帐户记录也删除了
                accounts = await list_accounts(db)
                assert len(accounts) == 1
                assert accounts[0].name == "bob"

        _run(_test())


# ---------------------------------------------------------------------------
# 场景 5：并发写入不损坏数据
# ---------------------------------------------------------------------------


class TestConcurrentWrites:
    """多个并发写入操作的数据完整性。"""

    def test_concurrent_writes_no_corruption(self, tmp_path: Path):
        """10 个并发 create_account 全部成功，记录数量正确。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                # 并发创建 10 个帐户
                tasks = [
                    create_account(db, f"user-{i}", f"key-{i}")
                    for i in range(10)
                ]
                results = await asyncio.gather(*tasks)

                # 验证所有记录都创建成功
                assert len(results) == 10
                for i, r in enumerate(results):
                    assert r.name == f"user-{i}"
                    assert r.apikey == f"key-{i}"
                    assert r.id == i + 1

                # 列出全部，数量一致
                all_accounts = await list_accounts(db)
                assert len(all_accounts) == 10
                names = {a.name for a in all_accounts}
                assert names == {f"user-{i}" for i in range(10)}

        _run(_test())


# ---------------------------------------------------------------------------
# 场景 6：全新数据库自动建表
# ---------------------------------------------------------------------------


class TestAutoCreateTables:
    """首次打开数据库时自动创建三张表。"""

    def test_fresh_db_auto_creates_tables(self, tmp_path: Path):
        """打开一个全新的 db 文件后，三张表均可正常操作。"""
        db_path = str(tmp_path / "test.db")

        # 确认文件尚不存在
        assert not Path(db_path).exists()

        async def _test():
            async with get_db(db_path) as db:
                # 三张表都应存在且可用：
                # - accounts
                await create_account(db, "test", "key")
                accounts = await list_accounts(db)
                assert len(accounts) == 1

                # - settings
                assert await get_setting(db, "foo") is None
                await set_setting(db, "foo", "bar")
                assert await get_setting(db, "foo") == "bar"

                # - servers
                await create_server_record(
                    db, account_id=1, server_id=1, product_id=1, region_id=1,
                )
                servers = await list_servers_by_account(db, 1)
                assert len(servers) == 1

        _run(_test())

        # 确认文件已创建
        assert Path(db_path).exists()


# ---------------------------------------------------------------------------
# 场景 7：迁移 v8 — 添加 13 个新列
# ---------------------------------------------------------------------------


class TestMigrationV8:
    """v8 迁移：为 servers 表添加 13 个新列（country, city, ip_type,
    root, password, cpu, ram, diskData, diskMedia, traffic,
    startTime, endTime, isAutoRenew）。"""

    def test_migration_v8_adds_all_columns(self, tmp_path: Path):
        """Given: 已创建 servers 表的数据库.
        When: 运行 migrate_db 迁移.
        Then: PRAGMA table_info 显示全部 13 个新列。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                # 先创建记录以触发表创建
                await create_account(db, "test", "key")
                await create_server_record(
                    db, account_id=1, server_id=1, product_id=1, region_id=1,
                )
                # 运行迁移
                await migrate_db(db)

                # 查询所有列
                rows = list(await db.execute_fetchall(
                    "PRAGMA table_info('servers')",
                ))
                columns = {r["name"] for r in rows}  # pyright: ignore[reportAny]

                expected = {
                    "country", "city", "ip_type", "root", "password",
                    "cpu", "ram", "diskData", "diskMedia", "traffic",
                    "startTime", "endTime", "isAutoRenew",
                }
                missing = expected - columns
                assert not missing, f"Missing columns: {missing}"

        _run(_test())

    def test_server_record_has_new_fields(self):
        """Given: 无.
        When: 用 13 个新字段的值实例化 ServerRecord.
        Then: 所有属性值与传入值一致。"""
        srv = ServerRecord(
            id=1,
            account_id=1,
            server_id=100,
            product_id=1,
            region_id=1,
            country="US",
            city="New York",
            ip_type="ipv4",
            root="root",
            password="secret",
            cpu=4,
            ram=8192,
            diskData=0,
            diskMedia="SSD",
            traffic=1000,
            startTime="2025-01-01",
            endTime="2026-01-01",
            isAutoRenew=1,
        )
        assert srv.country == "US"
        assert srv.city == "New York"
        assert srv.ip_type == "ipv4"
        assert srv.root == "root"
        assert srv.password == "secret"
        assert srv.cpu == 4
        assert srv.ram == 8192
        assert srv.diskData == 0
        assert srv.diskMedia == "SSD"
        assert srv.traffic == 1000
        assert srv.startTime == "2025-01-01"
        assert srv.endTime == "2026-01-01"
        assert srv.isAutoRenew == 1

    def test_create_server_record_with_geo(self, tmp_path: Path):
        """Given: 已创建帐户的数据库.
        When: 调用 create_server_record 传入 country/city/ip_type.
        Then: 返回的记录和重新查询的记录都包含正确的地理信息，未传字段为默认值。"""
        db_path = str(tmp_path / "test.db")

        async def _test():
            async with get_db(db_path) as db:
                await create_account(db, "alice", "key-aaaa")

                srv = await create_server_record(
                    db,
                    account_id=1,
                    server_id=200,
                    product_id=1,
                    region_id=1,
                    country="CN",
                    city="Shanghai",
                    ip_type="ipv4",
                )
                assert srv.country == "CN"
                assert srv.city == "Shanghai"
                assert srv.ip_type == "ipv4"

                # 重新查询验证持久化
                retrieved = await get_server_record(db, srv.id)
                assert retrieved is not None
                assert retrieved.country == "CN"
                assert retrieved.city == "Shanghai"
                assert retrieved.ip_type == "ipv4"
                # 未传入的字段应有默认值
                assert retrieved.root == ""
                assert retrieved.password == ""
                assert retrieved.cpu == 0
                assert retrieved.ram == 0
                assert retrieved.diskData == 0

        _run(_test())
