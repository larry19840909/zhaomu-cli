"""admin/tests/test_settings_routes.py — 设置管理 CRUD 路由测试。

使用 FastAPI TestClient + 临时 SQLite 数据库，覆盖全部 6 个端点：
- SC1: 账户 CRUD 完整生命周期
- SC2: 设置密码 → verify_password 验证通过
- SC3: 空 apikey → 422
- SC4: 列表 apikey 遮罩格式
- SC5: 删除账户级联删除服务器
- SC6: SOS 令牌设置与遮罩
"""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, TypeVar

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.api_routes.settings import router
from admin.api_routes.shared import get_db as shared_get_db
from admin.crypto import verify_password
from admin.db import (
    create_server_record,
    get_db as admin_get_db,
    get_setting,
    list_servers_by_account,
)

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    """运行协程 — 用于测试中直接访问 DB（绕过 API）。"""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 直接 DB 访问辅助
# ---------------------------------------------------------------------------


async def _get_password_hash(db_path: str) -> str | None:
    """直接从 settings 表读取 password_hash（绕过 API）。"""
    async with admin_get_db(db_path) as db:
        return await get_setting(db, "password_hash")


async def _count_servers(db_path: str, account_id: int) -> int:
    """返回指定账户下的服务器数量。"""
    async with admin_get_db(db_path) as db:
        servers = await list_servers_by_account(db, account_id)
        return len(servers)


async def _create_servers(db_path: str, account_id: int, count: int) -> None:
    """为指定账户创建若干服务器记录。"""
    async with admin_get_db(db_path) as db:
        for i in range(count):
            _ = await create_server_record(
                db,
                account_id=account_id,
                server_id=100 + i,
                product_id=1,
                region_id=1,
                ip=f"10.0.0.{i + 1}",
            )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """每个测试使用独立的临时 SQLite 数据库。"""
    return str(tmp_path / "test_admin.db")


@pytest.fixture
def app(temp_db_path: str) -> FastAPI:
    """FastAPI 应用 — 将 get_db 依赖重定向到临时数据库。"""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        async with admin_get_db(temp_db_path) as db:
            yield db

    app.dependency_overrides[shared_get_db] = override_get_db
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """FastAPI TestClient — 同步调用内部透明处理异步端点。"""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 测试场景
# ---------------------------------------------------------------------------


class TestSettingsRoutes:
    """设置管理 CRUD 路由集成测试。"""

    # — SC1: 账户 CRUD 完整生命周期 ————————————————

    def test_create_list_delete_account(self, client: TestClient):
        """创建账户 → 列表出现 → 删除 → 列表消失。"""
        # Create
        resp = client.post(
            "/api/accounts",
            json={"name": "test-acc", "apikey": "sk-1234567890abcdef"},
        )
        assert resp.status_code == 200
        created = resp.json()
        assert created["name"] == "test-acc"
        assert created["id"] == 1
        account_id: int = created["id"]

        # List — 应包含刚创建的账户
        resp = client.get("/api/accounts")
        assert resp.status_code == 200
        accounts = resp.json()
        assert len(accounts) == 1
        assert accounts[0]["id"] == account_id

        # Delete
        resp = client.delete(f"/api/accounts/{account_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # List after delete — 应为空
        resp = client.get("/api/accounts")
        assert resp.status_code == 200
        assert resp.json() == []

    # — SC2: 设置密码 → verify_password 验证 —————————

    def test_set_password_and_verify(self, client: TestClient, temp_db_path: str):
        """PUT 密码后，存储的哈希可通过 crypto.verify_password 验证。"""
        password = "admin-secret-p@ss!"
        resp = client.put(
            "/api/settings/password",
            json={"new_password": password},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        # 直接从 DB 读取哈希并验证正确性
        pwd_hash = _run(_get_password_hash(temp_db_path))
        assert pwd_hash is not None
        assert pwd_hash.startswith("$argon2id$")
        assert verify_password(password, pwd_hash) is True
        assert verify_password("wrong", pwd_hash) is False

        # GET /api/settings 报告 has_password=True
        resp = client.get("/api/settings")
        assert resp.status_code == 200
        assert resp.json()["has_password"] is True

    # — SC3: 空 apikey → 422 ————————————————————————

    def test_create_account_empty_apikey_returns_422(self, client: TestClient):
        """Pydantic min_length=1 校验：空 apikey 触发 422。"""
        resp = client.post("/api/accounts", json={"name": "bad", "apikey": ""})
        assert resp.status_code == 422

    # — SC4: 列表 apikey 遮罩 ————————————————————————

    def test_list_accounts_shows_masked_apikey(self, client: TestClient):
        """apikey 仅展示前 4 + 后 4 位，中间为 ****。"""
        apikey = "zhaomu-api-key-12345-abcde"
        _ = client.post("/api/accounts", json={"name": "mask-test", "apikey": apikey})

        resp = client.get("/api/accounts")
        assert resp.status_code == 200
        accounts = resp.json()
        assert len(accounts) == 1
        masked: str = accounts[0]["apikey_masked"]
        # "zhaomu-api-key-12345-abcde" → 前4="zhao"，后4="bcde"
        assert masked == "zhao****bcde"

    # — SC5: 删除账户级联删除服务器 ————————————————————

    def test_delete_account_cascades_servers(
        self, client: TestClient, temp_db_path: str,
    ):
        """删除账户后，其关联的服务器记录也被级联清理。"""
        # 创建账户
        resp = client.post(
            "/api/accounts",
            json={"name": "cascade-test", "apikey": "sk-cascade"},
        )
        account_id: int = resp.json()["id"]

        # 直接为账户创建 3 台服务器记录
        _run(_create_servers(temp_db_path, account_id, 3))
        assert _run(_count_servers(temp_db_path, account_id)) == 3

        # 通过 API 删除账户
        resp = client.delete(f"/api/accounts/{account_id}")
        assert resp.status_code == 200

        # ON DELETE CASCADE 应清理全部服务器
        assert _run(_count_servers(temp_db_path, account_id)) == 0

    # — SC6: SOS 令牌遮罩 ————————————————————————————

    def test_set_sos_token_and_get_masked(self, client: TestClient):
        """PUT SOS 令牌后，GET /api/settings 返回遮罩后的值。"""
        token = "sos-emergency-token-2024"
        resp = client.put("/api/settings/sos-token", json={"token": token})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        resp = client.get("/api/settings")
        assert resp.status_code == 200
        data = resp.json()
        # "sos-emergency-token-2024" → 前4="sos-"，后4="2024"
        assert data["sos_token_masked"] == "sos-****2024"
