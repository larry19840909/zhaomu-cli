"""朝暮数据 Web 管理后台客户端。

通过 Playwright 模拟登录获取 Yii2 session cookie，
之后使用 requests 调用 Web 管理后台接口（如流量用量查询）。
"""

import base64
import json
import os
import stat
import time
from pathlib import Path
from typing import Any

import requests

from zhaomu.errors import AuthError, APIError, NetworkError

DEFAULT_SESSION_FILE = str(Path.home() / ".zhaomu" / "session.json")
LOGIN_URL = "https://www.zhaomu.com/login/index"
MANAGE_BASE = "https://www.zhaomu.com/manage"
MAX_RELOGIN_RETRIES = 1

# Yii2 框架的认证 cookie（均为 HttpOnly）
AUTH_COOKIES = {"_identity-frontend", "advanced-frontend", "_csrf-frontend"}


def _obfuscate(text: str) -> str:
    """对凭据进行 base64 编码（可逆编码，非加密）。
    
    注意：这不是加密，任何能读取 session.json 的人都可以解码凭据。
    真实的密码安全依赖于文件系统权限（0600）和用户目录隔离。
    """
    return base64.b64encode(text.encode()).decode()


def _deobfuscate(encoded: str) -> str:
    """解码 base64 凭据。"""
    try:
        return base64.b64decode(encoded).decode()
    except Exception:
        return ""


def _ensure_dir(path: str) -> None:
    """创建目录（如果不存在）并设置权限 0700。"""
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
        try:
            os.chmod(dirname, stat.S_IRWXU)
        except OSError:
            pass


def _write_session_file(filepath: str, data: dict) -> None:
    """写入 session 文件并设置权限 0600。"""
    _ensure_dir(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


class ZhaomuWebClient:
    """朝暮数据 Web 管理后台客户端。

    通过 Playwright 模拟登录获取 Yii2 session cookie（_identity-frontend 等），
    之后使用 requests 调用 Web 管理后台接口（如流量用量查询）。
    cookie 过期后自动使用存储的凭据重新登录。
    """

    def __init__(self, session_file: str | None = None):
        self._session_file = session_file or DEFAULT_SESSION_FILE
        self._http = requests.Session()
        self._session_data: dict[str, Any] = {}
        self._relogin_count = 0

        # 加载已有 session
        try:
            with open(self._session_file, "r", encoding="utf-8") as f:
                self._session_data = json.load(f)
            self._load_cookies_from_session()
        except (FileNotFoundError, json.JSONDecodeError):
            self._session_data = {}

    # ------------------------------------------------------------------
    # Session 持久化
    # ------------------------------------------------------------------

    def _load_cookies_from_session(self):
        """将 session 文件中的 cookie 加载到 requests.Session。"""
        cookies = self._session_data.get("cookies", [])
        for c in cookies:
            self._http.cookies.set(
                c["name"], c["value"],
                domain=c.get("domain", ""),
                path=c.get("path", "/"),
            )

    def _save_session(self, cookies: list[dict[str, str]]):
        """保存 cookie 到 session 文件（保留已有凭据）。"""
        data = {"cookies": cookies}
        # 保留已有的凭据
        for key in ("username", "password"):
            if key in self._session_data:
                data[key] = self._session_data[key]
        _write_session_file(self._session_file, data)
        self._session_data = data
        self._http.cookies.clear()
        self._load_cookies_from_session()

    # ------------------------------------------------------------------
    # 凭据管理
    # ------------------------------------------------------------------

    def has_credentials(self) -> bool:
        """检查是否存储了登录凭据（用户名+密码）。"""
        return bool(
            self._session_data.get("username")
            and self._session_data.get("password")
        )

    def store_credentials(self, username: str, password: str):
        """存储编码后的登录凭据到 session 文件。"""
        data = dict(self._session_data)
        data["username"] = _obfuscate(username)
        data["password"] = _obfuscate(password)
        self._session_data = data
        _write_session_file(self._session_file, data)

    def get_username(self) -> str:
        """获取用户名（解码）。"""
        return _deobfuscate(self._session_data.get("username", ""))

    def get_password(self) -> str:
        """获取密码（解码）。"""
        return _deobfuscate(self._session_data.get("password", ""))

    def has_session(self) -> bool:
        """检查是否有可用的 session cookie。"""
        cookies = self._session_data.get("cookies", [])
        cookie_names = {c["name"] for c in cookies}
        return bool(AUTH_COOKIES & cookie_names)

    # ------------------------------------------------------------------
    # 登录
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> bool:
        """使用 Playwright 登录并保存 cookie。

        Args:
            username: 朝暮数据用户名/邮箱/手机号
            password: 登录密码

        Returns:
            True 表示登录成功。

        Raises:
            AuthError: 登录失败时抛出。
        """
        try:
            from playwright.sync_api import sync_playwright, Error as PlaywrightError
        except ImportError:
            raise AuthError("playwright 未安装，请运行: pip install playwright && playwright install chromium")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except PlaywrightError as e:
                msg = str(e)
                if "Executable doesn't exist" in msg or "not found" in msg.lower():
                    raise AuthError(
                        "Chromium 浏览器未安装，请运行: playwright install chromium"
                    )
                raise AuthError(f"启动浏览器失败：{e}")

            context = browser.new_context()
            page = context.new_page()

            try:
                page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

                # 填写登录表单（Yii2 登录页：用户名 + 密码 + 记住登录 + 登录按钮）
                username_input = page.locator(
                    'input[placeholder*="用户名"], input[placeholder*="邮箱"], '
                    'input[placeholder*="手机号"], input[name*="login"], '
                    'input[name*="username"]'
                ).first
                password_input = page.locator(
                    'input[placeholder*="密码"], input[name*="password"]'
                ).first
                login_button = page.locator('button:has-text("登录")')

                username_input.fill(username)
                password_input.fill(password)

                # 勾选"记住登录状态"（label 覆盖了 checkbox，用 force=True）
                checkbox = page.locator('input[type="checkbox"]').first
                if checkbox.is_visible():
                    try:
                        checkbox.check(force=True)
                    except Exception:
                        pass  # 可能默认已勾选，忽略失败

                login_button.click()

                # 等待登录完成（跳转到管理后台）
                page.wait_for_url("**/manage/**", timeout=15000)

                # 等待页面稳定，确保 cookie 完全写入
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                # 提取所有 zhaomu 相关 cookie（包括 HttpOnly）
                all_cookies = context.cookies()
                zhaomu_cookies = [
                    {
                        "name": c.get("name", ""),
                        "value": c.get("value", ""),
                        "domain": c.get("domain", ""),
                        "path": c.get("path", "/"),
                    }
                    for c in all_cookies
                    if "zhaomu.com" in (c.get("domain") or "")
                ]

                if not any(c["name"] in AUTH_COOKIES for c in zhaomu_cookies):
                    raise AuthError("登录失败：未获取到有效的认证 cookie")

                # 保存凭据和 cookie
                self.store_credentials(username, password)
                self._save_session(zhaomu_cookies)

                return True

            except Exception as e:
                if isinstance(e, AuthError):
                    raise
                raise AuthError(f"登录失败：{e}")
            finally:
                browser.close()

    # ------------------------------------------------------------------
    # HTTP 请求
    # ------------------------------------------------------------------

    def _request(self, path: str, params: dict | None = None) -> Any:
        """发送 GET 请求到 Web 管理后台，session 过期自动重登（最多 1 次）。

        Args:
            path: 相对于 MANAGE_BASE 的路径（如 "/accelerator/get-monitor"）
            params: URL 查询参数
        """
        url = f"{MANAGE_BASE}{path}"

        try:
            resp = self._http.get(url, params=params, allow_redirects=False, timeout=30)
        except requests.exceptions.Timeout:
            raise NetworkError(f"请求 {path} 超时")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"连接失败：{e}")

        # 会话过期检测：被重定向到登录页
        if resp.status_code in (301, 302, 303):
            location = resp.headers.get("Location", "")
            if "login" in location.lower():
                return self._try_relogin_and_retry(path, params)
            # 重定向到其他页面（如维护页）
            raise AuthError(f"Web 后台重定向至非预期地址: {location}")

        if resp.status_code == 401:
            return self._try_relogin_and_retry(path, params)

        if resp.status_code == 403:
            raise AuthError("无权限访问该资源")

        if resp.status_code == 404:
            raise APIError(404, "资源不存在")

        if not resp.ok:
            raise APIError(resp.status_code, resp.text[:500] or f"HTTP {resp.status_code}")

        try:
            return resp.json()
        except requests.exceptions.JSONDecodeError:
            raise APIError(resp.status_code, f"非 JSON 响应：{resp.text[:200]}")

    def _try_relogin_and_retry(self, path: str, params: dict | None) -> Any:
        """尝试重新登录后重试请求，最多 1 次。"""
        if self._relogin_count >= MAX_RELOGIN_RETRIES:
            raise AuthError("Web 会话已过期，自动重登失败")
        if not self.has_credentials():
            raise AuthError("Web 会话已过期，且未存储登录凭据")
        self._relogin_count += 1
        self.relogin()
        return self._request(path, params)

    def relogin(self):
        """使用存储的凭据自动重新登录。"""
        username = self.get_username()
        password = self.get_password()
        if not username or not password:
            raise AuthError("自动重登失败：未找到登录凭据")
        self.login(username, password)

    # ------------------------------------------------------------------
    # 业务方法
    # ------------------------------------------------------------------

    def traffic_usage(self, accelerator_id: int) -> list[dict[str, Any]]:
        """获取加速器的每日流量用量。

        URL: GET /manage/accelerator/get-monitor?id={accelerator_id}

        Args:
            accelerator_id: 加速器 ID

        Returns:
            流量用量记录列表，每项包含 Date（Unix 时间戳）、
            Traffic（GB）、BillingState（"Yes"/"No"）。响应非列表时返回空列表。

        Example:
            >>> client.traffic_usage(2242)
            [{"Date": 1782921600, "Traffic": 66, "BillingState": "No"}, ...]
        """
        data = self._request("/accelerator/get-monitor", params={"id": accelerator_id})
        if isinstance(data, list):
            return data
        return []

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def close(self):
        """关闭 HTTP 会话。"""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
