"""admin/server.py — FastAPI app with auth + static files for zhaomu admin panel.

提供：
- Bearer token 认证（argon2id 密码哈希 + session token）
- 首次启动模式（无密码时放行所有请求，需 ADMIN_INIT_TOKEN）
- CORS 中间件（允许 Vite dev server）
- 静态文件服务（dev: 本地目录, prod: _MEIPASS）
- 所有路由模块占位（settings, filter, products, orders, servers）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from admin.crypto import hash_password, verify_password
from admin.db import get_db, get_setting, migrate_db, set_setting


# ---------------------------------------------------------------------------
# 静态文件目录
# ---------------------------------------------------------------------------


def get_static_dir() -> Path:
    """获取前端静态文件目录。"""
    meipass: str | None = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass) / "frontend" / "dist"
    return Path(__file__).resolve().parent / "frontend" / "dist"


# ---------------------------------------------------------------------------
# 数据库辅助 — session token / password / username 读写
# ---------------------------------------------------------------------------


async def _load_session(db_path: str) -> str | None:
    """加载当前 session token，无 session 时返回 None。"""
    async with get_db(db_path) as db:
        return await get_setting(db, "admin_session")


async def _save_session(db_path: str, token: str) -> None:
    """写入 session token。"""
    async with get_db(db_path) as db:
        await set_setting(db, "admin_session", token)


async def _load_password_hash(db_path: str) -> str | None:
    """加载密码哈希，未设置时返回 None。"""
    async with get_db(db_path) as db:
        return await get_setting(db, "admin_password_hash")


async def _save_password_hash(db_path: str, pwd_hash: str) -> None:
    """写入密码哈希。"""
    async with get_db(db_path) as db:
        await set_setting(db, "admin_password_hash", pwd_hash)


async def _load_username(db_path: str) -> str | None:
    """加载管理员用户名。"""
    async with get_db(db_path) as db:
        return await get_setting(db, "admin_username")


async def _save_username(db_path: str, username: str) -> None:
    """写入管理员用户名。"""
    async with get_db(db_path) as db:
        await set_setting(db, "admin_username", username)


# ---------------------------------------------------------------------------
# SHA-256 向后兼容验证（旧格式 salt:hash → 自动升级为 argon2id）
# ---------------------------------------------------------------------------


def _verify_legacy(password: str, username: str, stored_blob: str) -> bool:
    """验证旧版 SHA-256 格式密码（salt_b64:hash_b64）。"""
    try:
        salt_b64, _ = stored_blob.split(":", 1)
        salt = base64.b64decode(salt_b64)
    except Exception:
        return False
    payload = salt + username.encode("utf-8") + password.encode("utf-8")
    expected = hashlib.sha256(payload).digest()
    try:
        _, hash_b64 = stored_blob.rsplit(":", 1)
        actual = base64.b64decode(hash_b64)
    except Exception:
        return False
    return hmac.compare_digest(expected, actual)


# ---------------------------------------------------------------------------
# 应用工厂
# ---------------------------------------------------------------------------


def create_app(
    db_path: str | None = None,
    static_dir: str | Path | None = None,
) -> FastAPI:
    """创建 FastAPI 应用实例。

    Args:
        db_path: 数据库文件路径，None 时使用 ADMIN_DB_PATH 环境变量，默认为 admin.db。
        static_dir: 静态文件目录，None 时使用 get_static_dir() 自动检测。
    """
    if db_path is None:
        db_path = os.environ.get("ADMIN_DB_PATH", "admin.db")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """应用生命周期：迁移数据库、加载 session、密码哈希、用户名。"""
        app.state.admin_db_path = db_path  # pyright: ignore[reportAttributeAccessIssue,reportAny]
        # 启动时执行数据库迁移（仅一次，避免每个请求都运行 ~28 条 SQL）
        async with get_db(db_path) as db:
            await migrate_db(db)
        app.state.admin_session = await _load_session(db_path)  # pyright: ignore[reportAttributeAccessIssue,reportAny]
        app.state.admin_pwd_hash = await _load_password_hash(db_path)  # pyright: ignore[reportAttributeAccessIssue,reportAny]
        app.state.admin_username = await _load_username(db_path)  # pyright: ignore[reportAttributeAccessIssue,reportAny]
        yield

    app = FastAPI(lifespan=lifespan)

    # -------------------------------------------------------------------
    # CORS 中间件 — 可通过 CORS_ORIGINS 环境变量配置（逗号分隔）
    # -------------------------------------------------------------------
    cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------------------
    # Auth 中间件
    # -------------------------------------------------------------------
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next: Any) -> Response:
        """Bearer token 认证中间件。

        - /api/auth/login 始终放行
        - 非 /api/ 路径（静态文件）不拦截 — SPA 前端自行处理登录 UI
        - 首次启动（无密码）放行所有请求
        - 其他 API 请求验证 Authorization: Bearer <token>
        """
        # 登录接口不拦截
        if request.url.path == "/api/auth/login":
            return await call_next(request)

        # 静态文件不拦截（SPA 前端自行管理登录 UI）
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        stored_session: str | None = request.app.state.admin_session  # pyright: ignore[reportAny]

        # 首次启动模式 — 仅放行登录和设置查询
        if stored_session is None:
            if request.url.path in ("/api/auth/login", "/api/settings"):
                return await call_next(request)
            return JSONResponse(status_code=403, content={"detail": "请先设置管理密码"})

        # 验证 Bearer session token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "缺少或无效的 Authorization 头"},
            )

        token = auth_header[7:]
        if not hmac.compare_digest(token, stored_session):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token 无效或已过期"},
            )

        return await call_next(request)

    # -------------------------------------------------------------------
    # 路由模块
    # -------------------------------------------------------------------

    # --- Auth ---
    auth_router = APIRouter(tags=["auth"])

    # 首次启动保护 token（可通过环境变量 ADMIN_INIT_TOKEN 设置）
    _INIT_TOKEN = os.environ.get("ADMIN_INIT_TOKEN", "")

    @auth_router.post("/api/auth/login")
    async def login(request: Request) -> dict[str, str]:
        """管理员登录 — argon2id 验证 + session token。"""
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=422, detail="无效的 JSON 请求体")
        username = body.get("username", "").strip()
        password = body.get("password", "")
        if not username:
            raise HTTPException(status_code=400, detail="用户名不能为空")
        if not password:
            raise HTTPException(status_code=400, detail="密码不能为空")

        stored_pwd_hash: str | None = app.state.admin_pwd_hash  # pyright: ignore[reportAny]
        stored_username: str | None = app.state.admin_username  # pyright: ignore[reportAny]

        if stored_pwd_hash is None:
            # 首次启动 — 检查 init token
            if _INIT_TOKEN:
                provided_init = body.get("init_token", "")
                if not hmac.compare_digest(provided_init, _INIT_TOKEN):
                    raise HTTPException(status_code=403, detail="首次设置需要有效的 INIT TOKEN")
            # 设置用户名和密码（argon2id）
            pwd_hash = hash_password(password)
            await _save_username(app.state.admin_db_path, username)  # pyright: ignore[reportAny]
            await _save_password_hash(app.state.admin_db_path, pwd_hash)  # pyright: ignore[reportAny]
            app.state.admin_username = username  # pyright: ignore[reportAny]
            app.state.admin_pwd_hash = pwd_hash  # pyright: ignore[reportAny]

        else:
            # 验证用户名
            if stored_username and not hmac.compare_digest(username.encode(), stored_username.encode()):
                raise HTTPException(status_code=401, detail="用户名或密码错误")

            # 验证密码：优先 argon2id，回退旧 SHA-256 格式
            if stored_pwd_hash.startswith("$argon2id$"):
                if not verify_password(password, stored_pwd_hash):
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
            elif ":" in stored_pwd_hash:
                # 旧 SHA-256 格式 → 验证并自动升级
                if not _verify_legacy(password, stored_username or "", stored_pwd_hash):
                    raise HTTPException(status_code=401, detail="用户名或密码错误")
                # 升级为 argon2id
                new_hash = hash_password(password)
                await _save_password_hash(app.state.admin_db_path, new_hash)  # pyright: ignore[reportAny]
                app.state.admin_pwd_hash = new_hash  # pyright: ignore[reportAny]
            else:
                raise HTTPException(status_code=500, detail="密码存储格式异常")

        # 生成 session token
        session_token = secrets.token_urlsafe(32)
        await _save_session(app.state.admin_db_path, session_token)  # pyright: ignore[reportAny]
        app.state.admin_session = session_token  # pyright: ignore[reportAny]

        return {"token": session_token, "username": stored_username or username}

    app.include_router(auth_router)

    # --- Filter ---
    from admin.api_routes.filter import router as filter_router
    app.include_router(filter_router)

    # --- Products ---
    from admin.api_routes.products import router as products_router
    app.include_router(products_router)

    # --- Orders ---
    from admin.api_routes.orders import router as orders_router
    app.include_router(orders_router)

    # --- Servers ---
    from admin.api_routes.servers import router as servers_router
    app.include_router(servers_router)

    # --- Settings ---
    from admin.api_routes.settings import router as settings_router
    app.include_router(settings_router)

    # --- Balance ---
    from admin.api_routes.balance import router as balance_router
    app.include_router(balance_router)

    # -------------------------------------------------------------------
    # 静态文件目录
    # -------------------------------------------------------------------
    resolved_static_dir = Path(static_dir) if static_dir else get_static_dir()

    # -------------------------------------------------------------------
    # SPA fallback + 静态文件 — 单一路由处理，不回退到 mount
    # -------------------------------------------------------------------
    from fastapi.responses import FileResponse

    @app.api_route("/{path:path}", methods=["GET", "HEAD"])
    async def spa_fallback(request: Request, path: str) -> Any:
        if path.startswith("api/"):
            raise HTTPException(status_code=404)
        file_path = resolved_static_dir / path
        if "." in path.split("/")[-1]:
            # 带扩展名 → 尝试直接返回静态文件
            if file_path.exists():
                headers: dict[str, str] = {}
                # 为 hashed 资源添加长期缓存（Vite 构建产物带 content hash）
                ext = path.rsplit(".", 1)[-1] if "." in path else ""
                if ext in ("js", "css", "woff", "woff2", "ttf", "svg", "png", "jpg", "ico"):
                    headers["Cache-Control"] = "public, max-age=31536000, immutable"
                return FileResponse(file_path, headers=headers)
            raise HTTPException(status_code=404)
        # SPA 页面路径 → 返回 index.html
        return FileResponse(resolved_static_dir / "index.html")

    return app


# ---------------------------------------------------------------------------
# 默认应用实例 — 供 uvicorn 直接引用（uvicorn admin.server:app）
# ---------------------------------------------------------------------------

app = create_app()
