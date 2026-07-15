"""admin/tests/test_orders_routes.py — 两阶段下单路由测试。

7 个场景覆盖 prepare 和 order 两个端点：
- SC1: prepare → order 单次下单成功，记录写入 DB
- SC2: 批量 3 单全部成功
- SC3: payment_cycle < minPaymentCycle → 返回失败结果
- SC4: 无效 product_id → 返回失败结果
- SC5: 不存在的账户 → 404
- SC6: 认证失败 → 500，无部分写入
- SC7: 批量下单其中 1 单失败 → 部分成功
"""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.api_routes.orders import router
from admin.api_routes.shared import get_db as shared_get_db
from admin.db import (
    create_account,
    get_db as admin_get_db,
    list_servers_by_account,
)
from zhaomu.errors import APIError, AuthError

T = type("T", (), {})


def _run(coro: Coroutine[Any, Any, Any]) -> Any:
    """在当前事件循环中运行协程。"""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Mock 对象工厂
# ---------------------------------------------------------------------------


def _make_product(**overrides: Any) -> MagicMock:
    """创建模拟 CloudProduct 对象。"""
    p = MagicMock()
    p.id = 9723
    p.cpu = 2
    p.ram = 4096
    p.disk = 40
    p.diskMax = 200
    p.diskData = 0
    p.diskDataMax = 0
    p.diskMedia = "SSD"
    p.bandwidth = None
    p.bandwidthMax = None
    p.traffic = 1000
    p.priceHour = 0.05
    p.price = 30
    p.priceQuarter = 85
    p.priceHalfYear = 160
    p.priceYear = 300
    p.tags = ""
    p.outOfStock = 0
    p.noWindows = None
    p.region_id = 780
    p.minPaymentCycle = 1
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


def _make_image(img_id: int, name: str, typ: str = "linux") -> MagicMock:
    """创建模拟 Image 对象。"""
    img = MagicMock()
    img.id = img_id
    img.name = name
    img.type = typ
    return img


def _make_op_result(
    success: bool, message: str, info: dict[str, Any] | None = None,
) -> MagicMock:
    """创建模拟 OperationResult 对象。"""
    r = MagicMock()
    r.success = success
    r.message = message
    r.info = info
    return r


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_path(tmp_path: Path) -> str:
    """每个测试使用独立的临时 SQLite 数据库。"""
    return str(tmp_path / "test_orders.db")


@pytest.fixture
def app_with_account(temp_db_path: str) -> FastAPI:
    """FastAPI 应用 — get_db 重定向到临时数据库，预创建账户 id=1。"""
    # 预创建账户
    async def _seed():
        async with admin_get_db(temp_db_path) as db:
            await create_account(db, "test-account", "test-apikey-12345")

    _run(_seed())

    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        async with admin_get_db(temp_db_path) as db:
            yield db

    app.dependency_overrides[shared_get_db] = override_get_db
    return app


@pytest.fixture
def app_no_account(temp_db_path: str) -> FastAPI:
    """FastAPI 应用 — 无预创建账户（用于 SC5 测试）。"""
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        async with admin_get_db(temp_db_path) as db:
            yield db

    app.dependency_overrides[shared_get_db] = override_get_db
    return app


@pytest.fixture
def client_with_account(app_with_account: FastAPI) -> TestClient:
    """FastAPI TestClient — 带预创建账户。"""
    return TestClient(app_with_account)


@pytest.fixture
def client_no_account(app_no_account: FastAPI) -> TestClient:
    """FastAPI TestClient — 无预创建账户。"""
    return TestClient(app_no_account)


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------


class TestPrepareOrder:
    """GET /api/orders/prepare/{product_id} 测试。"""

    def test_prepare_returns_product_and_images(
        self, client_with_account: TestClient,
    ) -> None:
        """prepare 返回产品信息、镜像列表和默认配置。"""
        mock_client = MagicMock()
        mock_client.product.info.return_value = _make_product(id=9723)
        mock_client.cloud.images.return_value = [
            _make_image(167, "Ubuntu 20.04", "linux"),
            _make_image(168, "Debian 11", "linux"),
        ]

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.get(
                "/api/orders/prepare/9723?account_id=1&apikey=test-key",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["product"]["id"] == 9723
        assert len(data["images"]) == 2
        assert data["images"][0]["id"] == 167
        assert data["images"][1]["id"] == 168
        assert data["defaultImageId"] == 167
        assert data["minPaymentCycle"] == 1
        assert data["defaultDisk"] == 40
        assert data["diskMax"] == 200


class TestSingleOrderSuccess:
    """SC1: prepare → order 单次下单成功，记录写入 DB。"""

    def test_single_order_succeeds_with_db_record(
        self, client_with_account: TestClient, temp_db_path: str,
    ) -> None:
        """下单成功后，DB 中存在对应的 server 记录。

        Given: 账户 id=1 存在，API 返回成功订单
        When: POST /api/orders 提交 1 个订单
        Then: 返回 success_count=1，DB 中有 1 条记录
        """
        mock_client = MagicMock()
        mock_client.product.info.return_value = _make_product(
            id=9723, region_id=780, minPaymentCycle=1,
        )
        mock_client.cloud.order.return_value = _make_op_result(
            success=True, message="下单成功", info={"id": 280722},
        )

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[{
                    "product_id": 9723,
                    "image_id": 167,
                    "disk": 40,
                    "payment_cycle": 1,
                }],
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is True
        assert data["results"][0]["server_id"] == 280722

        # 验证 DB 中有一条记录
        async def _check():
            async with admin_get_db(temp_db_path) as db:
                servers = await list_servers_by_account(db, 1)
                return len(servers)

        count = _run(_check())
        assert count == 1


class TestBatchThreeOrders:
    """SC2: 批量 3 单全部成功。"""

    def test_batch_three_orders_all_succeed(
        self, client_with_account: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 账户存在，API 返回 3 个成功订单
        When: POST /api/orders 提交 3 个订单
        Then: success_count=3，DB 中有 3 条记录
        """
        mock_client = MagicMock()
        # product.info 对每个 product_id 返回对应产品
        products = {
            9723: _make_product(id=9723, region_id=780),
            9724: _make_product(id=9724, region_id=780),
            9725: _make_product(id=9725, region_id=781),
        }

        def _info(pid: int) -> MagicMock:
            return products[pid]

        mock_client.product.info.side_effect = _info

        # cloud.order 依次返回成功结果
        mock_client.cloud.order.side_effect = [
            _make_op_result(True, "ok", {"id": 100}),
            _make_op_result(True, "ok", {"id": 101}),
            _make_op_result(True, "ok", {"id": 102}),
        ]

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[
                    {"product_id": 9723, "image_id": 167, "disk": 40, "payment_cycle": 1},
                    {"product_id": 9724, "image_id": 168, "disk": 50, "payment_cycle": 2},
                    {"product_id": 9725, "image_id": 169, "disk": 60, "payment_cycle": 3},
                ],
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 3
        assert len(data["results"]) == 3
        for r in data["results"]:
            assert r["success"] is True

        # 验证 DB 中有 3 条记录
        async def _check():
            async with admin_get_db(temp_db_path) as db:
                servers = await list_servers_by_account(db, 1)
                return len(servers)

        count = _run(_check())
        assert count == 3


class TestInvalidPaymentCycle:
    """SC3: payment_cycle < minPaymentCycle → 返回失败结果。"""

    def test_payment_cycle_below_minimum_returns_failure(
        self, client_with_account: TestClient,
    ) -> None:
        """Given: 产品 minPaymentCycle=2，但请求 payment_cycle=1
        When: POST /api/orders
        Then: 返回 success_count=0，results 中含失败项
        """
        mock_client = MagicMock()
        mock_client.product.info.return_value = _make_product(
            id=9723, minPaymentCycle=2,
        )
        # cloud.order 不应被调用
        mock_client.cloud.order = MagicMock()

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[{
                    "product_id": 9723,
                    "image_id": 167,
                    "disk": 40,
                    "payment_cycle": 1,
                }],
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 0
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is False
        assert "最低支付周期" in data["results"][0]["message"]
        # cloud.order 未被调用
        mock_client.cloud.order.assert_not_called()


class TestInvalidProductId:
    """SC4: 无效 product_id → 返回失败结果。"""

    def test_invalid_product_id_returns_failure(
        self, client_with_account: TestClient,
    ) -> None:
        """Given: product.info() 抛出 APIError
        When: POST /api/orders
        Then: 返回 success_count=0，results 中含失败项
        """
        mock_client = MagicMock()
        mock_client.product.info.side_effect = APIError(400, "产品不存在")
        mock_client.cloud.order = MagicMock()

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[{
                    "product_id": 99999,
                    "image_id": 167,
                    "disk": 40,
                    "payment_cycle": 1,
                }],
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 0
        assert len(data["results"]) == 1
        assert data["results"][0]["success"] is False
        assert "99999" in data["results"][0]["message"]
        mock_client.cloud.order.assert_not_called()


class TestNonexistentAccount:
    """SC5: 不存在的账户 → 404。"""

    def test_nonexistent_account_returns_404(
        self, client_no_account: TestClient,
    ) -> None:
        """Given: 数据库中无账户 id=99
        When: POST /api/orders?account_id=99
        Then: 返回 404
        """
        resp = client_no_account.post(
            "/api/orders?account_id=99&apikey=test-key",
            json=[{
                "product_id": 9723,
                "image_id": 167,
                "disk": 40,
                "payment_cycle": 1,
            }],
        )

        assert resp.status_code == 404
        assert "99" in resp.json()["detail"]


class TestAuthErrorNoPartialWrites:
    """SC6: 认证失败 → 500，无部分写入。"""

    def test_auth_error_returns_500_no_partial_writes(
        self, client_with_account: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 账户存在，但 API 抛出 AuthError
        When: POST /api/orders 提交 3 个订单，第一个就触发 AuthError
        Then: 返回 500，DB 中无任何记录
        """
        mock_client = MagicMock()
        mock_client.product.info.return_value = _make_product(id=9723)
        mock_client.cloud.order.side_effect = AuthError("无效的 API Key")

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[
                    {"product_id": 9723, "image_id": 167, "disk": 40, "payment_cycle": 1},
                    {"product_id": 9724, "image_id": 168, "disk": 50, "payment_cycle": 1},
                    {"product_id": 9725, "image_id": 169, "disk": 60, "payment_cycle": 1},
                ],
            )

        assert resp.status_code == 500
        assert "认证失败" in resp.json()["detail"]

        # 验证 DB 中无任何记录
        async def _check():
            async with admin_get_db(temp_db_path) as db:
                servers = await list_servers_by_account(db, 1)
                return len(servers)

        count = _run(_check())
        assert count == 0


class TestPartialBatchSuccess:
    """SC7: 批量下单其中 1 单失败 → 部分成功。"""

    def test_batch_with_one_failure_partial_success(
        self, client_with_account: TestClient, temp_db_path: str,
    ) -> None:
        """Given: 账户存在，API 对第 2 个订单返回 APIError
        When: POST /api/orders 提交 3 个订单
        Then: success_count=2，DB 中有 2 条记录
        """
        mock_client = MagicMock()
        mock_client.product.info.return_value = _make_product(
            id=9723, region_id=780,
        )
        mock_client.cloud.order.side_effect = [
            _make_op_result(True, "ok", {"id": 100}),
            APIError(400, "余额不足"),
            _make_op_result(True, "ok", {"id": 102}),
        ]

        with patch(
            "admin.api_routes.orders.get_client", return_value=mock_client,
        ):
            resp = client_with_account.post(
                "/api/orders?account_id=1&apikey=test-key",
                json=[
                    {"product_id": 9723, "image_id": 167, "disk": 40, "payment_cycle": 1},
                    {"product_id": 9723, "image_id": 168, "disk": 50, "payment_cycle": 1},
                    {"product_id": 9723, "image_id": 169, "disk": 60, "payment_cycle": 1},
                ],
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success_count"] == 2
        assert len(data["results"]) == 3
        assert data["results"][0]["success"] is True
        assert data["results"][0]["server_id"] == 100
        assert data["results"][1]["success"] is False
        assert "余额不足" in data["results"][1]["message"]
        assert data["results"][2]["success"] is True
        assert data["results"][2]["server_id"] == 102

        # 验证 DB 中有 2 条记录（第 2 条未写入）
        async def _check():
            async with admin_get_db(temp_db_path) as db:
                servers = await list_servers_by_account(db, 1)
                return servers

        servers = _run(_check())
        assert len(servers) == 2
        server_ids = {s.server_id for s in servers}
        assert server_ids == {100, 102}
