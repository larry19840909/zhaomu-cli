"""admin/tests/test_servers_routes.py — 云服务器管理路由测试。

9 个场景覆盖 list/poll/deploy/destroy 端点：
- SC1: deploy 运行中服务器 → 200，状态更新为 deployed
- SC2: poll 更新状态 → 200，DB 状态更新
- SC3: destroy 成功 → 200，状态更新为 destroyed
- SC4: deploy 非 running → 400
- SC5: deploy 无 IP → 400
- SC6: destroy 已销毁 → 400
- SC7: 无 SOS token → 400
- SC8: deploy API 出错 → 500，状态不变
- SC9: resolve_region_id 失败 → 400
"""

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.api_routes.servers import router
from admin.api_routes.shared import get_db as shared_get_db
from admin.crypto import encrypt_secret
from admin.db import (
    create_account,
    create_server_record,
    get_db as admin_get_db,
    get_server_record,
    set_setting,
)
from zhaomu_deploy.models import DeployResult

T = TypeVar("T")


def _run(coro: Coroutine[Any, Any, T]) -> T:
    """运行协程 — 用于测试中直接访问 DB（绕过 API）。"""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# DB 操作辅助
# ---------------------------------------------------------------------------


async def _ensure_account(db_path: str) -> int:
    """创建测试账户并返回 account_id。"""
    async with admin_get_db(db_path) as db:
        rec = await create_account(db, "test-acc", "sk-test")
        return rec.id


async def _setup_sos_token(db_path: str, token: str) -> None:
    """在 settings 表中设置加密的 SOS token。"""
    async with admin_get_db(db_path) as db:
        await set_setting(db, "sos_token", encrypt_secret(token))


async def _create_running_server(
    db_path: str,
    server_id: int = 100,
    ip: str = "1.2.3.4",
    status: str = "running",
    account_id: int = 1,
) -> int:
    """创建一条服务器记录并返回 DB 内部 ID。"""
    async with admin_get_db(db_path) as db:
        rec = await create_server_record(
            db,
            account_id=account_id,
            server_id=server_id,
            product_id=1,
            region_id=1,
            image="Ubuntu 20.04",
            disk=30,
            payment_cycle=1,
            ip=ip,
            status=status,
        )
        return rec.id


async def _get_server_status(db_path: str, db_id: int) -> str | None:
    """读取服务器记录的 status 字段。"""
    async with admin_get_db(db_path) as db:
        rec = await get_server_record(db, db_id)
        return rec.status if rec else None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """每个测试使用独立的临时 SQLite 数据库。"""
    return str(tmp_path / "test_servers.db")


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
# Mock 工厂
# ---------------------------------------------------------------------------


def _make_cloud_detail_mock(
    cpu: int = 2,
    ram: int = 2048,
    disk: int = 30,
    password: str = "secret-pass",
    ip: str = "1.2.3.4",
    image: str = "Ubuntu 20.04",
) -> MagicMock:
    """创建 CloudServerDetail 的 MagicMock。"""
    m = MagicMock()
    m.cpu = cpu
    m.ram = ram
    m.disk = disk
    m.password = password
    m.ip = ip
    m.image = image
    return m


def _make_region_mock(city: str = "新加坡", cityEn: str = "Singapore") -> MagicMock:
    """创建 Region 的 MagicMock。"""
    m = MagicMock()
    m.city = city
    m.cityEn = cityEn
    return m


def _make_successful_deploy_mock(
    code: int = 200, msg: str = "deploy ok", ip: str = "10.0.0.1",
) -> MagicMock:
    """创建成功 DeployClient 的 MagicMock。"""
    m = MagicMock()
    m.create_deploy.return_value = DeployResult(code=code, msg=msg, ip=ip)
    return m


# ---------------------------------------------------------------------------
# 测试场景
# ---------------------------------------------------------------------------


class TestServerRoutes:
    """云服务器管理路由测试 — 9 个场景。"""

    # — SC1: deploy running server ————————————————————————————————————

    def test_deploy_running_server(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 运行中服务器 + SOS token 已配置
        When: POST /api/servers/{id}/deploy
        Then: 返回 200 success，DB 状态更新为 deployed
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-sos-token"))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        mock_client = MagicMock()
        mock_client.cloud.info.return_value = _make_cloud_detail_mock()
        mock_client.region.info.return_value = _make_region_mock()

        mock_deploy = _make_successful_deploy_mock()

        with (
            patch("admin.api_routes.servers.get_client", return_value=mock_client),
            patch("admin.api_routes.servers.DeployClient", return_value=mock_deploy),
        ):
            resp = client.post(
                f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["deploy_code"] == 200
        assert data["server_ip"] == "10.0.0.1"
        assert data["deployed_at"] != ""

        # DB 状态已更新
        status = _run(_get_server_status(temp_db_path, db_id))
        assert status == "deployed"

    # — SC2: poll updates status ——————————————————————————————————————

    def test_poll_updates_status(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: provisioning 状态 + IP 为空的服务器
        When: GET /api/servers/{id}/poll
        Then: 返回 200，状态更新为 running，IP 已填充
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(
            _create_running_server(temp_db_path, status="provisioning", ip="", account_id=account_id),
        )

        mock_client = MagicMock()
        detail = _make_cloud_detail_mock(cpu=1, ram=1024, disk=20, image="Debian 11")
        detail.status = 2  # running
        detail.ip = "5.6.7.8"
        mock_client.cloud.info.return_value = detail

        with patch("admin.api_routes.servers.get_client", return_value=mock_client):
            resp = client.get(
                f"/api/servers/{db_id}/poll?account_id=1&apikey=sk-test",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"
        assert data["ip"] == "5.6.7.8"
        assert data["live"]["live_status"] == "running"
        assert data["live"]["live_ip"] == "5.6.7.8"

        status = _run(_get_server_status(temp_db_path, db_id))
        assert status == "running"

    # — SC3: destroy succeeds ——————————————————————————————————————————

    def test_destroy_succeeds(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 运行中的服务器
        When: DELETE /api/servers/{id}
        Then: 返回 200 success，状态更新为 destroyed
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        mock_client = MagicMock()
        mock_client.cloud.destroy.return_value = MagicMock()

        with patch("admin.api_routes.servers.get_client", return_value=mock_client):
            resp = client.delete(
                f"/api/servers/{db_id}?account_id=1&apikey=sk-test",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["destroyed_at"] != ""

        status = _run(_get_server_status(temp_db_path, db_id))
        assert status == "destroyed"

    # — SC4: deploy non-running → 400 ———————————————————————————————————

    def test_deploy_non_running_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: status=provisioning 的服务器
        When: POST /api/servers/{id}/deploy
        Then: 返回 400，提示 not running
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-token"))
        db_id = _run(_create_running_server(temp_db_path, status="provisioning", account_id=account_id))

        resp = client.post(
            f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
        )

        assert resp.status_code == 400
        assert "not running" in resp.json()["detail"]

    # — SC5: deploy no IP → 400 ————————————————————————————————————————

    def test_deploy_no_ip_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: running 但 IP 为空的服务器
        When: POST /api/servers/{id}/deploy
        Then: 返回 400，提示 no IP
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-token"))
        db_id = _run(_create_running_server(temp_db_path, ip="", account_id=account_id))

        resp = client.post(
            f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
        )

        assert resp.status_code == 400
        assert "no IP" in resp.json()["detail"]

    # — SC6: destroy already-destroyed → 400 ———————————————————————————

    def test_destroy_already_destroyed_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: status=destroyed 的服务器
        When: DELETE /api/servers/{id}
        Then: 返回 400，提示 already destroyed
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, status="destroyed", account_id=account_id))

        resp = client.delete(
            f"/api/servers/{db_id}?account_id=1&apikey=sk-test",
        )

        assert resp.status_code == 400
        assert "already destroyed" in resp.json()["detail"]

    # — SC7: no SOS token → 400 ————————————————————————————————————————

    def test_deploy_no_sos_token_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: SOS token 未配置
        When: POST /api/servers/{id}/deploy
        Then: 返回 400，提示 SOS token not configured
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        resp = client.post(
            f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
        )

        assert resp.status_code == 400
        assert "SOS token" in resp.json()["detail"]

    # — SC8: deploy API error → 500 status unchanged ——————————————————

    def test_deploy_api_error_returns_500_status_unchanged(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 运行中服务器 + SOS token，但 MetroVPN API 不可用
        When: POST /api/servers/{id}/deploy
        Then: 返回 500，服务器状态保持 running
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-token"))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        mock_client = MagicMock()
        mock_client.cloud.info.return_value = _make_cloud_detail_mock(
            cpu=1, ram=1024, disk=20,
        )
        mock_client.region.info.return_value = _make_region_mock()

        mock_deploy = MagicMock()
        mock_deploy.create_deploy.side_effect = RuntimeError("MetroVPN down")

        with (
            patch("admin.api_routes.servers.get_client", return_value=mock_client),
            patch("admin.api_routes.servers.DeployClient", return_value=mock_deploy),
        ):
            resp = client.post(
                f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
            )

        assert resp.status_code == 500
        assert "MetroVPN" in resp.json()["detail"]

        # DB 状态未变
        status = _run(_get_server_status(temp_db_path, db_id))
        assert status == "running"

    # — SC9: resolve_region_id fails → 400 —————————————————————————————

    def test_resolve_region_id_fails_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 地域名称不在 MetroVPN 映射表中
        When: POST /api/servers/{id}/deploy
        Then: 返回 400，提示无法解析地域
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-token"))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        mock_client = MagicMock()
        mock_client.cloud.info.return_value = _make_cloud_detail_mock()
        mock_client.region.info.return_value = _make_region_mock(
            city="未知城市", cityEn="UnknownCity",
        )

        with (
            patch("admin.api_routes.servers.get_client", return_value=mock_client),
            patch(
                "admin.api_routes.servers.resolve_region_id",
                side_effect=ValueError("unknown city 'UnknownCity'"),
            ),
        ):
            resp = client.post(
                f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
            )

        assert resp.status_code == 400
        assert "无法解析" in resp.json()["detail"]
