"""测试 filter 路由 — 6 个场景覆盖 deploy region 筛选和产品对比。"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from admin.api_routes.filter import router

# 导入 _REGION_LOOKUP 用于测试断言
try:
    from zhaomu_deploy.client import (  # pyright: ignore[reportMissingImports]
        _REGION_LOOKUP,  # pyright: ignore[reportPrivateUsage]
    )
except ImportError:
    _REGION_LOOKUP: dict[str, str] = {}  # pyright: ignore[reportConstantRedefinition]

from zhaomu.errors import APIError


# ---------------------------------------------------------------------------
# 测试用的 region 数据（模拟 zhaomu API 返回）
# ---------------------------------------------------------------------------

def _make_region(id: int, city: str, cityEn: str, zone: str, country: str = "中国") -> MagicMock:
    """创建模拟 Region 对象。"""
    r = MagicMock()
    r.id = id
    r.city = city
    r.cityEn = cityEn
    r.zone = zone
    r.country = country
    return r


def _make_compare_item(target_id: int, name: str, explain: str) -> MagicMock:
    """创建模拟 CompareItem 对象。"""
    c = MagicMock()
    c.target_id = target_id
    c.name = name
    c.explain = explain
    return c


# ---------------------------------------------------------------------------
# FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture
def app() -> FastAPI:
    """创建仅挂载 filter 路由的测试用 FastAPI 应用。"""
    _app = FastAPI()
    _app.include_router(router)
    return _app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """FastAPI TestClient。"""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------

class TestFilterRegions:
    """GET /api/filter/regions 测试。"""

    def test_returns_deploy_supported_subset(
        self, client: TestClient,
    ) -> None:
        """SC1: 获取 deploy 支持的 region — 只返回在 _REGION_LOOKUP 中的地域。

        Given: zhaomu API 返回 3 个地域，其中 2 个在 deploy 映射表中
        When: 调用 GET /api/filter/regions
        Then: 只返回映射表中的 2 个地域，不包括不在映射表中的那一个
        """
        # _REGION_LOOKUP 包含中文 "新加坡" (-> "singapore") 和英文 "tokyo" (-> "Tokyo")
        # 确保至少两个 key 命中
        assert "新加坡" in _REGION_LOOKUP or _patch_region_lookup_with({"新加坡", "tokyo"})

        mock_client = MagicMock()
        mock_client.region.list.return_value = [
            _make_region(1, "新加坡", "Singapore", "A", "新加坡"),       # city 命中
            _make_region(2, "东京", "tokyo", "B", "日本"),              # cityEn 命中
            _make_region(3, "未映射城市", "UnmappedCity", "C", "未知"), # 不在映射表中
        ]

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get("/api/filter/regions?account_id=1&apikey=test")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = {r["id"] for r in data}
        assert ids == {1, 2}
        # 不在映射表中的 region 被排除
        assert 3 not in ids


def _patch_region_lookup_with(keys: set[str]) -> bool:
    """临时补丁确保 _REGION_LOOKUP 包含指定 key（用于测试环境）。"""
    import admin.api_routes.filter as _m
    for k in keys:
        if k not in _m._REGION_LOOKUP:
            _m._REGION_LOOKUP[k] = f"mapped-{k}"
    return True


class TestFilterRegionsExclude:
    """SC3: 不在 deploy map 中的 region 被排除。"""

    def test_region_not_in_deploy_map_excluded(
        self, client: TestClient,
    ) -> None:
        """Given: zhaomu API 返回的 region 的 city/cityEn 均不在映射表中
        When: 调用 GET /api/filter/regions
        Then: 该 region 不出现在返回结果中
        """
        mock_client = MagicMock()
        mock_client.region.list.return_value = [
            _make_region(99, "未知城市", "UnknownCity", "X", "未知"),
        ]

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get("/api/filter/regions?account_id=1&apikey=test")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0


class TestDeployModuleUnavailable:
    """SC5: deploy 模块不可用时优雅降级。"""

    def test_empty_result_when_lookup_missing(
        self, client: TestClient,
    ) -> None:
        """Given: _REGION_LOOKUP 为空（模拟 import 失败降级）
        When: 调用 GET /api/filter/regions
        Then: 返回空列表，不抛异常
        """
        mock_client = MagicMock()
        mock_client.region.list.return_value = [
            _make_region(1, "新加坡", "Singapore", "A"),
            _make_region(2, "东京", "tokyo", "B"),
        ]

        with (
            patch("admin.api_routes.filter.get_client", return_value=mock_client),
            patch("admin.api_routes.filter._REGION_LOOKUP", {}),
        ):
            resp = client.get("/api/filter/regions?account_id=1&apikey=test")

        assert resp.status_code == 200
        assert resp.json() == []


class TestCompareFeatures:
    """GET /api/filter/regions/{region_id}/compare 测试。"""

    def test_compare_returns_features_with_name_explain(
        self, client: TestClient,
    ) -> None:
        """SC2: compare 返回带 name/explanation 的功能列表和 region 信息。

        Given: product.compare() 返回 2 个 CompareItem，region.info() 返回合法地域
        When: 调用 GET /api/filter/regions/1/compare
        Then: 响应包含 features 数组和 region_info
        """
        mock_client = MagicMock()
        mock_client.product.compare.return_value = [
            _make_compare_item(10, "带宽", "100Mbps"),
            _make_compare_item(27, "IP更换", "支持更换IP"),
        ]
        mock_region = _make_region(1, "新加坡", "Singapore", "A")
        mock_client.region.info.return_value = mock_region

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get("/api/filter/regions/1/compare?account_id=1&apikey=test")

        assert resp.status_code == 200
        data = resp.json()
        assert "features" in data
        assert "region_info" in data
        assert len(data["features"]) == 2
        # 第一个 feature 是"带宽"，非 IP 非退款 → "other"
        assert data["features"][0]["category"] == "other"
        assert data["features"][0]["name"] == "带宽"
        assert data["features"][0]["explanation"] == "100Mbps"
        # 第二个 feature target_id=27 → "ip_type"
        assert data["features"][1]["category"] == "ip_type"
        assert data["region_info"]["id"] == 1
        assert data["region_info"]["city"] == "新加坡"

    def test_refund_in_name_matched_to_refund_category(
        self, client: TestClient,
    ) -> None:
        """SC4: compare 中 name 包含"退款"时被正确分类为 refund。

        Given: CompareItem name 包含"退款"，target_id 不是 27
        When: 调用 GET /api/filter/regions/1/compare
        Then: 该 feature 的 category 为 "refund"
        """
        mock_client = MagicMock()
        mock_client.product.compare.return_value = [
            _make_compare_item(50, "24小时销毁退款", "购买24小时内可销毁退款"),
        ]
        mock_region = _make_region(1, "新加坡", "Singapore", "A")
        mock_client.region.info.return_value = mock_region

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get("/api/filter/regions/1/compare?account_id=1&apikey=test")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["features"]) == 1
        assert data["features"][0]["category"] == "refund"
        assert "退款" in data["features"][0]["name"]

    def test_partial_api_error_still_returns_features(
        self, client: TestClient,
    ) -> None:
        """SC6: region.info() 调用失败时仍返回 features（优雅降级）。

        Given: product.compare() 正常返回，但 region.info() 抛出 APIError
        When: 调用 GET /api/filter/regions/1/compare
        Then: 仍返回 features，region_info 使用降级默认值
        """
        mock_client = MagicMock()
        mock_client.product.compare.return_value = [
            _make_compare_item(10, "带宽", "100Mbps"),
        ]
        mock_client.region.info.side_effect = APIError(500, "region info 不可用")

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get("/api/filter/regions/1/compare?account_id=1&apikey=test")

        assert resp.status_code == 200
        data = resp.json()
        # features 仍然返回
        assert len(data["features"]) == 1
        assert data["features"][0]["name"] == "带宽"
        # region_info 降级为部分数据
        assert data["region_info"]["id"] == 1
        assert data["region_info"]["city"] == ""
