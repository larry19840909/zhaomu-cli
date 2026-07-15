"""测试 products 路由 — 6 个场景覆盖多地域去重与筛选。

SC1: 两个地域相同产品 → 去重保留最低价 + 合并 zones
SC2: outOfStock 产品被排除
SC3: os=windows 时排除 noWindows 产品
SC4: cpu 精确匹配筛选
SC5: 所有地域无有效产品 → 返回 200 空列表
SC6: 一个地域 API 报错 → 其他地域仍返回结果
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.api_routes.products import router
from zhaomu.errors import APIError


# ---------------------------------------------------------------------------
# 测试辅助函数
# ---------------------------------------------------------------------------

def _make_product(
    id: int,
    cpu: int = 2,
    ram: int = 2048,
    disk: int = 40,
    diskMax: int = 100,
    traffic: int = 1000,
    diskMedia: str = "SSD",
    price: int = 50,
    priceQuarter: int = 140,
    priceHalfYear: int = 260,
    priceYear: int = 480,
    tags: str = "",
    outOfStock: int = 0,
    noWindows: int | None = None,
) -> MagicMock:
    """创建模拟 CloudProduct 对象。"""
    p = MagicMock()
    p.id = id
    p.cpu = cpu
    p.ram = ram
    p.disk = disk
    p.diskMax = diskMax
    p.traffic = traffic
    p.diskMedia = diskMedia
    p.price = price
    p.priceQuarter = priceQuarter
    p.priceHalfYear = priceHalfYear
    p.priceYear = priceYear
    p.tags = tags
    p.outOfStock = outOfStock
    p.noWindows = noWindows
    return p


# ---------------------------------------------------------------------------
# FastAPI TestClient fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app() -> FastAPI:
    """创建仅挂载 products 路由的测试用 FastAPI 应用。"""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """FastAPI TestClient。"""
    return TestClient(app)


# ===================================================================
# SC1: 两个地域相同产品 → 去重保留最低价 + 合并 zones
# ===================================================================

class TestDedupTwoRegions:
    """SC1: 两个地域相同产品 → 去重保留最低价 + 合并 zones。"""

    def test_two_regions_same_product_dedup_with_min_price(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 和 region 2 有相同规格 (2C/2G/40G/CN2) 但价格不同
        When: GET /api/products?region_ids=1,2
        Then: 只返回一个条目，价格取最低，zones 包含两个 region
        """
        mock_client = MagicMock()
        mock_client.product.list.side_effect = lambda rid: {
            1: [_make_product(101, cpu=2, ram=2048, disk=40, price=60, tags="CN2")],
            2: [_make_product(201, cpu=2, ram=2048, disk=40, price=50, tags="CN2")],
        }[rid]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=1,2")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["price"] == 50
        assert data[0]["cpu"] == 2
        assert data[0]["ram"] == 2048
        assert data[0]["disk"] == 40
        assert data[0]["zones"] == [1, 2]


# ===================================================================
# SC2: outOfStock 产品被排除
# ===================================================================

class TestOutOfStockExcluded:
    """SC2: outOfStock 产品被排除。"""

    def test_out_of_stock_product_excluded(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 有 2 个产品，一个 outOfStock=1
        When: GET /api/products?region_ids=1
        Then: outOfStock=1 的产品不在结果中
        """
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, outOfStock=0),
            _make_product(2, cpu=4, ram=4096, disk=80, price=100, outOfStock=1),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=1")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cpu"] == 2


# ===================================================================
# SC3: os=windows 时排除 noWindows 产品
# ===================================================================

class TestNoWindowsWithOsFilter:
    """SC3: os=windows 时排除 noWindows 产品。"""

    def test_no_windows_product_excluded_when_os_is_windows(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 有 noWindows=1 产品和正常产品
        When: GET /api/products?region_ids=1&os=windows
        Then: noWindows=1 的产品被排除
        """
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, noWindows=None),
            _make_product(2, cpu=4, ram=4096, disk=80, price=100, noWindows=1),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get(
                "/api/products?account_id=1&apikey=t&region_ids=1&os=windows",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cpu"] == 2

    def test_no_windows_product_included_when_os_is_linux(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 有 noWindows=1 产品和正常产品
        When: GET /api/products?region_ids=1&os=linux
        Then: noWindows=1 也返回（linux 不触发排除逻辑）
        """
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, noWindows=None),
            _make_product(2, cpu=4, ram=4096, disk=80, price=100, noWindows=1),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get(
                "/api/products?account_id=1&apikey=t&region_ids=1&os=linux",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # 两者都返回


# ===================================================================
# SC4: cpu 精确匹配筛选
# ===================================================================

class TestCpuFilter:
    """SC4: cpu 精确匹配筛选。"""

    def test_cpu_exact_match_filter(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 有 1C、2C、4C 产品
        When: GET /api/products?region_ids=1&cpu=2
        Then: 只返回 cpu=2 的产品
        """
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=1, ram=1024, disk=20, price=30),
            _make_product(2, cpu=2, ram=2048, disk=40, price=50),
            _make_product(3, cpu=4, ram=4096, disk=80, price=100),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=1&cpu=2")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cpu"] == 2


# ===================================================================
# SC5: 所有地域无有效产品 → 返回 200 空列表
# ===================================================================

class TestAllEmpty:
    """SC5: 所有地域无有效产品 → 返回 200 空列表。"""

    def test_empty_result_when_all_out_of_stock(
        self, client: TestClient,
    ) -> None:
        """Given: 所有产品都 outOfStock=1
        When: GET /api/products?region_ids=1
        Then: 返回空列表，状态码 200
        """
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, outOfStock=1),
            _make_product(2, cpu=4, ram=4096, disk=80, price=100, outOfStock=1),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=1")

        assert resp.status_code == 200
        assert resp.json() == []

    def test_empty_region_ids_returns_empty(
        self, client: TestClient,
    ) -> None:
        """Given: region_ids 为空字符串
        When: GET /api/products?region_ids=
        Then: 返回空列表，不调用 API
        """
        mock_client = MagicMock()

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=")

        assert resp.status_code == 200
        assert resp.json() == []
        mock_client.product.list.assert_not_called()


# ===================================================================
# SC6: 一个地域 API 报错 → 其他地域仍返回结果
# ===================================================================

class TestPartialApiError:
    """SC6: 一个地域 API 报错 → 其他地域仍返回结果。"""

    def test_one_region_api_error_other_still_returned(
        self, client: TestClient,
    ) -> None:
        """Given: region 1 正常返回产品，region 2 抛 APIError
        When: GET /api/products?region_ids=1,2
        Then: region 1 的产品正常返回，不受 region 2 错误影响
        """
        mock_client = MagicMock()

        def _list(rid: int):
            if rid == 1:
                return [_make_product(101, cpu=2, ram=2048, disk=40, price=50)]
            if rid == 2:
                raise APIError(500, "region 2 不可用")
            return []

        mock_client.product.list.side_effect = _list

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get("/api/products?account_id=1&apikey=t&region_ids=1,2")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["zones"] == [1]


# ===================================================================
# 补充: traffic 筛选测试
# ===================================================================

class TestTrafficFilter:
    """traffic 参数筛选补充测试。"""

    def test_traffic_unlimited_returns_only_zero_traffic(
        self, client: TestClient,
    ) -> None:
        """traffic=unlimited 只返回 traffic==0 的产品。"""
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, traffic=0),
            _make_product(2, cpu=2, ram=2048, disk=40, price=60, traffic=1000),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get(
                "/api/products?account_id=1&apikey=t&region_ids=1&traffic=unlimited",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["traffic"] == 0

    def test_traffic_threshold_unlimited_passes(
        self, client: TestClient,
    ) -> None:
        """traffic=2000 时，不限量 (traffic=0) 也通过筛选。"""
        mock_client = MagicMock()
        mock_client.product.list.return_value = [
            _make_product(1, cpu=2, ram=2048, disk=40, price=50, traffic=0, tags="A"),
            _make_product(2, cpu=2, ram=2048, disk=40, price=60, traffic=1000, tags="B"),
            _make_product(3, cpu=2, ram=2048, disk=40, price=70, traffic=2000, tags="C"),
        ]

        with patch("admin.api_routes.products.get_client", return_value=mock_client):
            resp = client.get(
                "/api/products?account_id=1&apikey=t&region_ids=1&traffic=2000",
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # traffic=0 + traffic=2000
        traffics = {p["traffic"] for p in data}
        assert traffics == {0, 2000}
