"""admin/server.py — FastAPI app with auth + static files for zhaomu admin panel.

提供：
- Bearer token 认证（sha256 哈希 + base64 编码）
- 首次启动模式（无密码时放行所有请求）
- CORS 中间件（允许 Vite dev server）
- 静态文件服务（dev: 本地目录, prod: _MEIPASS）
- 所有路由模块占位（settings, filter, products, orders, servers）
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.responses import Response

from admin.db import get_db, get_setting, set_setting


# ---------------------------------------------------------------------------
# Token 计算 — sha256(password) → base64
# ---------------------------------------------------------------------------


def _compute_token(password: str) -> str:
    """计算 admin 认证 token。

    token = base64(sha256(password))，与数据库存储值一致。
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest).decode("ascii")


# ---------------------------------------------------------------------------
# 静态文件目录
# ---------------------------------------------------------------------------


def get_static_dir() -> Path:
    """获取前端静态文件目录。

    Prod（PyInstaller 打包）：sys._MEIPASS/frontend/dist
    Dev：项目根目录下的 frontend/dist
    """
    meipass: str | None = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass) / "frontend" / "dist"
    return Path(__file__).resolve().parent / "frontend" / "dist"


# ---------------------------------------------------------------------------
# 数据库辅助 — token 读写（复用 admin/db.py）
# ---------------------------------------------------------------------------


async def _load_token(db_path: str) -> str | None:
    """从数据库加载 admin_password_hash，未设置时返回 None。"""
    async with get_db(db_path) as db:
        return await get_setting(db, "admin_password_hash")


async def _save_token(db_path: str, token: str) -> None:
    """将 admin token 写入（或覆盖）到数据库。"""
    async with get_db(db_path) as db:
        await set_setting(db, "admin_password_hash", token)


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
        """应用生命周期：启动时加载 token。"""
        app.state.admin_db_path = db_path  # pyright: ignore[reportAttributeAccessIssue,reportAny]
        app.state.admin_token = await _load_token(db_path)  # pyright: ignore[reportAttributeAccessIssue,reportAny]
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

        stored_token: str | None = request.app.state.admin_token  # pyright: ignore[reportAny]

        # 首次启动模式 — 仅放行登录和设置查询
        if stored_token is None:
            if request.url.path in ("/api/auth/login", "/api/settings"):
                return await call_next(request)
            return JSONResponse(status_code=403, content={"detail": "请先设置管理密码"})

        # 验证 Bearer token
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "缺少或无效的 Authorization 头"},
            )

        token = auth_header[7:]  # 去掉 "Bearer " 前缀
        if not hmac.compare_digest(token, stored_token):
            return JSONResponse(
                status_code=401,
                content={"detail": "Token 无效"},
            )

        return await call_next(request)

    # -------------------------------------------------------------------
    # 路由模块
    # -------------------------------------------------------------------

    # --- Auth ---
    auth_router = APIRouter(tags=["auth"])

    class LoginRequest(BaseModel):
        password: str = Field(..., min_length=1)

    @auth_router.post("/api/auth/login")
    async def login(request: Request, body: LoginRequest) -> dict[str, str]:
        """管理员登录。

        首次登录设置密码，后续登录验证密码。
        Token = base64(sha256(password))，与数据库存储值一致。
        """
        password = body.password
        if not password:
            raise HTTPException(status_code=400, detail="密码不能为空")
        token = _compute_token(password)
        app_state = request.app.state
        stored_token: str | None = app_state.admin_token  # pyright: ignore[reportAny]

        if stored_token is None:
            # 首次启动 — 设置密码
            await _save_token(app_state.admin_db_path, token)  # pyright: ignore[reportAny]
            app_state.admin_token = token  # pyright: ignore[reportAny]
            return {"token": token}

        if not hmac.compare_digest(token, stored_token):
            raise HTTPException(status_code=401, detail="密码错误")

        return {"token": token}

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
