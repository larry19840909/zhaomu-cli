"""admin/tests/test_servers_routes.py — 云服务器管理路由测试。

18 个场景覆盖 list/poll/deploy/destroy/detail/delete-record 端点：
- SC1: deploy 运行中服务器 → 200，状态更新为 deployed
- SC2: poll 更新状态 → 200，DB 状态更新
- SC3: destroy 成功 → 200，状态更新为 destroyed
- SC4: deploy 非 running → 400
- SC5: deploy 无 IP → 400
- SC6: destroy 已销毁 → 400
- SC7: 无 SOS token → 400
- SC8: deploy API 出错 → 500，状态不变
- SC9: resolve_region_id 失败 → 400
- SC10: _server_to_dict 包含所有新字段
- SC11: filter by country
- SC12: filter by account_name
- SC13: filter multiple params AND logic
- SC14: filter by ip_type
- SC15: detail endpoint 返回 masked password
- SC16: detail endpoint 缓存到 DB
- SC17: delete record only for 已销毁
- SC18: delete record 404
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
    status: str = "运行中",
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


async def _update_server_fields(
    db_path: str, db_id: int, **fields: object,
) -> None:
    """直接更新服务器记录的字段（用于测试中设置新字段）。"""
    async with admin_get_db(db_path) as db:
        for field, val in fields.items():
            await db.execute(
                f"UPDATE servers SET {field} = ? WHERE id = ?",
                (val, db_id),
            )
        await db.commit()


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
    """创建 CloudServerDetail 的 MagicMock，包含所有 detail 字段。"""
    m = MagicMock()
    m.cpu = cpu
    m.ram = ram
    m.disk = disk
    m.password = password
    m.ip = ip
    m.image = image
    # 为 detail 端点需要的额外字段设默认值（防止 getattr 返回 MagicMock）
    m.root = "root"
    m.diskData = 0
    m.diskMedia = ""
    m.traffic = 0
    m.startTime = ""
    m.endTime = ""
    m.isAutoRenew = 0
    m.status = 2
    return m


def _make_region_mock(city: str = "新加坡", cityEn: str = "Singapore", country: str = "新加坡") -> MagicMock:
    """创建 Region 的 MagicMock。"""
    m = MagicMock()
    m.city = city
    m.cityEn = cityEn
    m.country = country
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

        # DB deploy_status 已更新为已部署，status 不变
        async def _get_deploy_status(db_path: str, db_id: int) -> str:
            async with admin_get_db(db_path) as db:
                rec = await get_server_record(db, db_id)
                return rec.deploy_status if rec else ""
        deploy_s = _run(_get_deploy_status(temp_db_path, db_id))
        assert deploy_s == "已部署"

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
        assert data["status"] == "运行中"
        assert data["ip"] == "5.6.7.8"
        assert data["live"]["live_status"] == "运行中"
        assert data["live"]["live_ip"] == "5.6.7.8"

        status = _run(_get_server_status(temp_db_path, db_id))
        assert status == "运行中"

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
        assert status == "已销毁"

    # — SC4: deploy non-running → 400 ———————————————————————————————————

    def test_deploy_non_running_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: status=provisioning 的服务器（非运行中）
        When: POST /api/servers/{id}/deploy
        Then: 返回 400，提示仅运行中的服务器可以部署
        """
        account_id = _run(_ensure_account(temp_db_path))
        _run(_setup_sos_token(temp_db_path, "test-token"))
        db_id = _run(_create_running_server(temp_db_path, status="provisioning", account_id=account_id))

        resp = client.post(
            f"/api/servers/{db_id}/deploy?account_id=1&apikey=sk-test",
        )

        assert resp.status_code == 400
        assert "运行中" in resp.json()["detail"]

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
        assert "no ip" in resp.json()["detail"].lower()

    # — SC6: destroy already-destroyed → 400 ———————————————————————————

    def test_destroy_already_destroyed_returns_400(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: status=destroyed 的服务器
        When: DELETE /api/servers/{id}
        Then: 返回 400，提示 already destroyed
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, status="已销毁", account_id=account_id))

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
        assert status == "运行中"

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

    # — SC10: _server_to_dict 包含所有新字段 ——————————————————————————

    def test_server_to_dict_includes_new_fields(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 服务器记录包含所有新字段（country, city, ip_type 等）
        When: GET /api/servers?account_id=1
        Then: 响应中的每条记录包含所有 14 个新字段
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))
        # 设置新字段
        _run(_update_server_fields(
            temp_db_path, db_id,
            country="新加坡", city="Singapore", ip_type="原生IP",
            root="root", password="secret123", cpu=4, ram=8192,
            diskData=50, diskMedia="SSD", traffic=2000,
            startTime="2025-01-01", endTime="2025-12-31",
            isAutoRenew=1, has_refund=0,
        ))

        resp = client.get(f"/api/servers?account_id={account_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        rec = data[0]
        assert rec["country"] == "新加坡"
        assert rec["city"] == "Singapore"
        assert rec["ip_type"] == "原生IP"
        assert rec["root"] == "root"
        assert "password" not in rec
        assert rec["cpu"] == 4
        assert rec["ram"] == 8192
        assert rec["diskData"] == 50
        assert rec["diskMedia"] == "SSD"
        assert rec["traffic"] == 2000
        assert rec["startTime"] == "2025-01-01"
        assert rec["endTime"] == "2025-12-31"
        assert rec["isAutoRenew"] == 1
        assert rec["has_refund"] == 0

    # — SC11: filter by country ————————————————————————————————————————

    def test_filter_by_country(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 两台服务器分别在新加坡和日本
        When: GET /api/servers?country=新加坡
        Then: 只返回新加坡的服务器
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id_sg = _run(_create_running_server(
            temp_db_path, server_id=100, account_id=account_id,
        ))
        db_id_jp = _run(_create_running_server(
            temp_db_path, server_id=200, account_id=account_id,
        ))
        _run(_update_server_fields(temp_db_path, db_id_sg, country="新加坡"))
        _run(_update_server_fields(temp_db_path, db_id_jp, country="日本"))

        resp = client.get(f"/api/servers?account_id={account_id}&country=新加坡")
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data]
        assert db_id_sg in ids
        assert db_id_jp not in ids

    # — SC12: filter by account_name ————————————————————————————————————

    def test_filter_by_account_name(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 两个账户各有一台服务器
        When: GET /api/servers?account_name=test-acc
        Then: 只返回该账户的服务器
        """
        acc1 = _run(_ensure_account(temp_db_path))
        # 创建第二个账户
        async def _create_acc2() -> int:
            async with admin_get_db(temp_db_path) as db:
                rec = await create_account(db, "other-acc", "sk-other")
                return rec.id
        acc2 = _run(_create_acc2())

        db_id_1 = _run(_create_running_server(
            temp_db_path, server_id=100, account_id=acc1,
        ))
        db_id_2 = _run(_create_running_server(
            temp_db_path, server_id=200, account_id=acc2,
        ))

        resp = client.get("/api/servers?account_name=test-acc")
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data]
        assert db_id_1 in ids
        assert db_id_2 not in ids

    # — SC13: filter multiple params AND logic ————————————————————————

    def test_filter_multiple_params_and_logic(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 两台服务器 country/ip_type 不同
        When: GET /api/servers?country=新加坡&deploy_status=已部署
        Then: 只返回同时满足两个条件的记录
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id_a = _run(_create_running_server(
            temp_db_path, server_id=100, account_id=account_id,
        ))
        db_id_b = _run(_create_running_server(
            temp_db_path, server_id=200, account_id=account_id,
        ))
        _run(_update_server_fields(
            temp_db_path, db_id_a, country="新加坡", deploy_status="已部署",
        ))
        _run(_update_server_fields(
            temp_db_path, db_id_b, country="日本", deploy_status="",
        ))

        resp = client.get(
            f"/api/servers?account_id={account_id}&country=新加坡&deploy_status=已部署",
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data]
        assert db_id_a in ids
        assert db_id_b not in ids

    # — SC14: filter by ip_type ————————————————————————————————————

    def test_filter_by_ip_type(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 两台服务器 ip_type 不同
        When: GET /api/servers?ip_type=原生IP
        Then: 只返回原生IP的服务器
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id_a = _run(_create_running_server(
            temp_db_path, server_id=100, account_id=account_id,
        ))
        db_id_b = _run(_create_running_server(
            temp_db_path, server_id=200, account_id=account_id,
        ))
        _run(_update_server_fields(temp_db_path, db_id_a, ip_type="原生IP"))
        _run(_update_server_fields(temp_db_path, db_id_b, ip_type="广播IP"))

        resp = client.get(
            f"/api/servers?account_id={account_id}&ip_type=原生IP",
        )
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data]
        assert db_id_a in ids
        assert db_id_b not in ids

    # — SC15: detail endpoint 返回 masked password ————————————————————

    def test_detail_endpoint_returns_masked_password(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 运行中服务器，zhaomu API 返回密码
        When: GET /api/servers/{id}/detail
        Then: 返回 ** 而非真实密码
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        detail_mock = _make_cloud_detail_mock(
            cpu=2, ram=2048, disk=30, password="real-password",
        )
        region_mock = _make_region_mock(city="新加坡", cityEn="Singapore")

        mock_client = MagicMock()
        mock_client.cloud.info.return_value = detail_mock
        mock_client.region.info.return_value = region_mock

        with patch("admin.api_routes.servers.get_client", return_value=mock_client):
            resp = client.get(f"/api/servers/{db_id}/detail?account_id=1&apikey=sk-test")

        assert resp.status_code == 200
        data = resp.json()
        assert data["password"] == "**"
        assert data["password_raw"] == "real-password"

    # — SC16: detail endpoint 缓存到 DB ——————————————————————————————————

    def test_detail_endpoint_caches_to_db(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 服务器记录无 detail 字段
        When: GET /api/servers/{id}/detail
        Then: DB 中的 cpu/ram/traffic 等字段被更新
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id = _run(_create_running_server(temp_db_path, account_id=account_id))

        detail_mock = _make_cloud_detail_mock(
            cpu=4, ram=4096, disk=40, password="secret", ip="1.2.3.4", image="Ubuntu 22.04",
        )
        detail_mock.diskData = 100
        detail_mock.diskMedia = "NVMe"
        detail_mock.traffic = 5000
        detail_mock.startTime = "2025-01-01"
        detail_mock.endTime = "2025-06-30"
        detail_mock.isAutoRenew = 1
        detail_mock.root = "root"

        region_mock = _make_region_mock(city="新加坡", cityEn="Singapore")

        mock_client = MagicMock()
        mock_client.cloud.info.return_value = detail_mock
        mock_client.region.info.return_value = region_mock

        with patch("admin.api_routes.servers.get_client", return_value=mock_client):
            resp = client.get(f"/api/servers/{db_id}/detail?account_id=1&apikey=sk-test")
        assert resp.status_code == 200

        # 验证 DB 已更新
        async def _get_server_fields() -> dict[str, object]:
            async with admin_get_db(temp_db_path) as db:
                rows = list(await db.execute_fetchall(
                    "SELECT cpu, ram, diskData, diskMedia, traffic, startTime, endTime,"
                    " isAutoRenew, root, password, country, city"
                    " FROM servers WHERE id = ?",
                    (db_id,),
                ))
                return dict(rows[0])  # pyright: ignore[reportAny]
        fields = _run(_get_server_fields())
        assert fields["cpu"] == 4
        assert fields["ram"] == 4096
        assert fields["diskData"] == 100
        assert fields["diskMedia"] == "NVMe"
        assert fields["traffic"] == 5000
        assert fields["startTime"] == "2025-01-01"
        assert fields["endTime"] == "2025-06-30"
        assert fields["isAutoRenew"] == 1
        assert fields["root"] == "root"
        assert fields["password"] == "secret"
        assert fields["country"] == "新加坡"

    # — SC17: delete record only for 已销毁 ————————————————————————————

    def test_delete_record_destroyed_only(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 一台已销毁服务器、一台运行中服务器
        When: DELETE /api/servers/{id}/record
        Then: 已销毁返回 200，运行中返回 400
        """
        account_id = _run(_ensure_account(temp_db_path))
        db_id_destroyed = _run(_create_running_server(
            temp_db_path, server_id=100, status="已销毁", account_id=account_id,
        ))
        db_id_running = _run(_create_running_server(
            temp_db_path, server_id=200, status="运行中", account_id=account_id,
        ))

        # 已销毁 → 200
        resp1 = client.delete(
            f"/api/servers/{db_id_destroyed}/record?account_id=1&apikey=sk-test",
        )
        assert resp1.status_code == 200
        assert resp1.json()["success"] is True

        # 运行中 → 400
        resp2 = client.delete(
            f"/api/servers/{db_id_running}/record?account_id=1&apikey=sk-test",
        )
        assert resp2.status_code == 400
        assert "已销毁" in resp2.json()["detail"]

    # — SC18: delete record not found ——————————————————————————————————

    def test_delete_record_not_found(
        self, client: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 不存在 id=9999 的记录
        When: DELETE /api/servers/9999/record
        Then: 返回 404
        """
        _ = _run(_ensure_account(temp_db_path))
        resp = client.delete(
            "/api/servers/9999/record?account_id=1&apikey=sk-test",
        )
        assert resp.status_code == 404
