"""测试 shared.py 模块的 ZhaomuClient 缓存行为。"""
from unittest.mock import MagicMock, patch

import pytest

from admin.api_routes.shared import _client_cache, clear_client, get_client


class TestClientCache:
    """ZhaomuClient 缓存行为测试 — 验证缓存逻辑，不使用真实 API 调用。"""

    @pytest.fixture(autouse=True)
    def _clear_cache(self) -> None:
        """每个测试前清空模块级缓存，确保测试隔离。"""
        _client_cache.clear()

    @patch("admin.api_routes.shared.ZhaomuClient")
    def test_same_account_returns_cached(self, mock_cls: MagicMock) -> None:
        """相同 account_id 应返回同一个缓存对象，不再创建新实例。"""
        mock_cls.return_value = MagicMock(name="client_A")

        client1 = get_client(1, "apikey_1")
        client2 = get_client(1, "apikey_1")

        assert client1 is client2
        mock_cls.assert_called_once_with(apikey="apikey_1")

    @patch("admin.api_routes.shared.ZhaomuClient")
    def test_different_accounts_return_different(self, mock_cls: MagicMock) -> None:
        """不同 account_id 应返回各自独立的客户端对象。"""
        client_a = MagicMock(name="client_A")
        client_b = MagicMock(name="client_B")
        mock_cls.side_effect = [client_a, client_b]

        result_a = get_client(1, "apikey_a")
        result_b = get_client(2, "apikey_b")

        assert result_a is not result_b
        assert result_a is client_a
        assert result_b is client_b

    @patch("admin.api_routes.shared.ZhaomuClient")
    def test_clear_removes_and_closes(self, mock_cls: MagicMock) -> None:
        """清除缓存应从字典移除客户端并调用其 close() 方法。"""
        mock_client = MagicMock(name="client")
        mock_cls.return_value = mock_client

        get_client(1, "apikey_1")
        clear_client(1)

        assert 1 not in _client_cache
        mock_client.close.assert_called_once()

    @patch("admin.api_routes.shared.ZhaomuClient")
    def test_get_creates_new_after_clear(self, mock_cls: MagicMock) -> None:
        """清除缓存后再次获取应创建新的客户端对象，而非复用旧对象。"""
        client_old = MagicMock(name="client_old")
        client_new = MagicMock(name="client_new")
        mock_cls.side_effect = [client_old, client_new]

        first = get_client(1, "apikey_1")
        clear_client(1)
        second = get_client(1, "apikey_1")

        assert first is client_old
        assert second is client_new
        assert first is not second
