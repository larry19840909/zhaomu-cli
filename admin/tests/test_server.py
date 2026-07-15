"""admin/tests/test_server.py — admin/server.py 的场景测试。

覆盖 7 个场景：
- SC1: 正确密码登录 → 200 + token
- SC2: 错误密码登录 → 401
- SC3: 认证通过后访问受保护路由 → 200
- SC4: 无 Authorization 头 → 401
- SC5: 无效 token → 401
- SC6: 首次启动（无密码）→ 任何请求通过
- SC7: 静态文件服务正常
"""

import base64
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from admin.server import create_app


# ---------------------------------------------------------------------------
# 辅助函数 — 与 server.py 的 _compute_token 逻辑一致
# ---------------------------------------------------------------------------


def _compute_token(password: str) -> str:
    """计算 admin token，供测试中使用。"""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """创建 TestClient，使用临时数据库。

    每个测试拥有独立的 db 文件，测试间完全隔离。
    """
    db_path = str(tmp_path / "admin.db")
    app = create_app(db_path)
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# 场景 1：正确密码登录 → 200 + token
# ---------------------------------------------------------------------------


class TestLoginCorrectPassword:
    """SC1: 登录正确密码。"""

    def test_login_correct_password_returns_token(self, client: TestClient) -> None:
        """首次登录应设置密码并返回有效 token。"""
        password = "my_correct_password"
        resp = client.post("/api/auth/login", json={"password": password})

        assert resp.status_code == 200
        data: dict = resp.json()
        assert "token" in data
        assert data["token"] == _compute_token(password)

    def test_relogin_with_correct_password_succeeds(self, client: TestClient) -> None:
        """再次用相同密码登录也应成功返回相同 token。"""
        password = "my_second_password"
        resp1 = client.post("/api/auth/login", json={"password": password})
        token1 = resp1.json()["token"]

        resp2 = client.post("/api/auth/login", json={"password": password})
        token2 = resp2.json()["token"]

        assert resp2.status_code == 200
        assert token1 == token2


# ---------------------------------------------------------------------------
# 场景 2：错误密码 → 401
# ---------------------------------------------------------------------------


class TestLoginWrongPassword:
    """SC2: 错误密码拒绝登录。"""

    def test_login_wrong_password_returns_401(self, client: TestClient) -> None:
        """错误密码应返回 401。"""
        # 先设置密码
        client.post("/api/auth/login", json={"password": "correct_pass"})
        # 用错误密码登录
        resp = client.post("/api/auth/login", json={"password": "wrong_pass"})

        assert resp.status_code == 401
        assert "密码错误" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 场景 3：认证通过后访问受保护的 API 路由 → 200
# ---------------------------------------------------------------------------


class TestAuthenticatedRequest:
    """SC3: 带有效 token 访问受保护的路由。"""

    def test_authenticated_filter_regions_returns_200(self, client: TestClient) -> None:
        """先登录获取 token，再用 token 访问 /api/filter/regions?account_id=1&apikey=t 应返回 200。"""
        # 登录
        login_resp = client.post("/api/auth/login", json={"password": "test_pass"})
        token = login_resp.json()["token"]

        mock_client = MagicMock()
        mock_client.region.list.return_value = []

        with patch("admin.api_routes.filter.get_client", return_value=mock_client):
            resp = client.get(
                "/api/filter/regions?account_id=1&apikey=t",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 场景 4：无 Authorization 头 → 401
# ---------------------------------------------------------------------------


class TestNoAuthHeader:
    """SC4: 无 token 访问 API 被拒绝。"""

    def test_no_auth_header_returns_401(self, client: TestClient) -> None:
        """密码已设置但没有携带 Authorization 头 → 401。"""
        # 先设置密码
        client.post("/api/auth/login", json={"password": "some_pass"})
        # 不带任何认证头
        resp = client.get("/api/filter/regions?account_id=1&apikey=t")

        assert resp.status_code == 401
        assert "缺少或无效" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 场景 5：无效 token → 401
# ---------------------------------------------------------------------------


class TestInvalidToken:
    """SC5: 无效 token 被拒绝。"""

    def test_invalid_token_returns_401(self, client: TestClient) -> None:
        """携带错误 token 访问应返回 401。"""
        # 先设置密码
        client.post("/api/auth/login", json={"password": "valid_pass"})
        # 使用错误的 token
        resp = client.get(
            "/api/filter/regions?account_id=1&apikey=t",
            headers={"Authorization": "Bearer invalid_token_value"},
        )

        assert resp.status_code == 401
        assert "Token 无效" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 场景 6：首次启动（无密码）→ 任何请求通过
# ---------------------------------------------------------------------------


class TestFirstStartupNoPassword:
    """SC6: 首次启动未设置密码时放行所有请求。"""

    def test_first_startup_no_password_any_request_accepted(
        self, tmp_path: Path,
    ) -> None:
        """未设置密码时，不带 token 的请求应直接通过。"""
        db_path = str(tmp_path / "fresh_admin.db")
        app = create_app(db_path)
        mock_client = MagicMock()
        mock_client.region.list.return_value = []
        with TestClient(app) as client:
            with patch("admin.api_routes.filter.get_client", return_value=mock_client):
                resp = client.get("/api/filter/regions?account_id=1&apikey=t")
            assert resp.status_code == 200

    def test_first_startup_no_password_with_any_token_accepted(
        self, tmp_path: Path,
    ) -> None:
        """未设置密码时，即使携带无效 token 也应通过。"""
        db_path = str(tmp_path / "fresh_admin2.db")
        app = create_app(db_path)
        mock_client = MagicMock()
        mock_client.region.list.return_value = []
        with TestClient(app) as client:
            with patch("admin.api_routes.filter.get_client", return_value=mock_client):
                resp = client.get(
                    "/api/filter/regions?account_id=1&apikey=t",
                    headers={"Authorization": "Bearer random_stuff"},
                )
            assert resp.status_code == 200

    def test_first_startup_login_sets_password(self, tmp_path: Path) -> None:
        """未设置密码时，首次登录应设置密码并返回 token，之后需认证。"""
        db_path = str(tmp_path / "fresh_admin3.db")

        # 首次登录
        app1 = create_app(db_path)
        with TestClient(app1) as client:
            login_resp = client.post(
                "/api/auth/login", json={"password": "initial_pass"},
            )
            assert login_resp.status_code == 200
            token = login_resp.json()["token"]

        # 再次创建 app（模拟重启），应加载 token
        app2 = create_app(db_path)
        mock_client = MagicMock()
        mock_client.region.list.return_value = []
        with TestClient(app2) as client:
            with patch("admin.api_routes.filter.get_client", return_value=mock_client):
                # 带 token 应通过
                resp = client.get(
                    "/api/filter/regions?account_id=1&apikey=t",
                    headers={"Authorization": f"Bearer {token}"},
                )
                assert resp.status_code == 200

                # 不带 token 应被拒绝
                resp2 = client.get("/api/filter/regions?account_id=1&apikey=t")
                assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# 场景 7：静态文件服务
# ---------------------------------------------------------------------------


class TestStaticFileServing:
    """SC7: 静态文件服务正常。"""

    def test_static_file_serving_in_dev(self, tmp_path: Path) -> None:
        """创建临时静态目录，验证文件可正常访问。"""
        # 创建临时静态目录
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        index_content = "<html><body>zhaomu admin</body></html>"
        _ = (static_dir / "index.html").write_text(index_content, encoding="utf-8")

        # 创建另一个子文件
        js_dir = static_dir / "assets"
        js_dir.mkdir()
        _ = (js_dir / "app.js").write_text("console.log('hello');", encoding="utf-8")

        db_path = str(tmp_path / "admin.db")
        app = create_app(db_path, static_dir=static_dir)
        with TestClient(app) as client:
            # 访问根路径（StaticFiles html=True 自动查找 index.html）
            resp = client.get("/")
            assert resp.status_code == 200
            assert index_content.encode("utf-8") in resp.content

            # 访问子文件
            resp2 = client.get("/assets/app.js")
            assert resp2.status_code == 200
            assert b"console.log" in resp2.content

    def test_static_files_bypass_auth(self, tmp_path: Path) -> None:
        """静态文件不经过 auth 中间件 — 即使设置了密码也应直接访问。"""
        # 创建静态文件
        static_dir = tmp_path / "static"
        static_dir.mkdir()
        _ = (static_dir / "index.html").write_text("<html></html>", encoding="utf-8")

        db_path = str(tmp_path / "admin.db")
        app = create_app(db_path, static_dir=static_dir)
        with TestClient(app) as client:
            # 先设置密码
            client.post("/api/auth/login", json={"password": "admin_pass"})

            # 不携带 token 访问静态文件仍应成功
            resp = client.get("/")
            assert resp.status_code == 200
