"""admin/api_routes/settings.py — 设置管理 CRUD 路由。

提供 6 个端点：
- GET  /api/settings          — 设置摘要（账户列表、SOS 令牌遮罩、密码状态）
- PUT  /api/settings/password — 设置/替换管理后台密码
- GET  /api/accounts          — 列出所有账户（apikey 遮罩）
- POST /api/accounts          — 创建账户（apikey 加密存储）
- DELETE /api/accounts/{id}   — 删除账户（级联删除关联服务器）
- PUT  /api/settings/sos-token — 设置 SOS 令牌（加密存储）
"""
from __future__ import annotations

import aiosqlite
import base64
import hashlib
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from admin.api_routes.shared import get_db, clear_client
from admin.crypto import decrypt_secret, encrypt_secret
from admin.db import (
    AccountRecord,
    create_account,
    delete_account,
    get_setting,
    list_accounts,
    set_setting,
)

router = APIRouter()

# 数据库 settings 表的键名
_KEY_PASSWORD_HASH = "admin_password_hash"
_KEY_SOS_TOKEN = "sos_token"


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def _mask(secret: str) -> str:
    """遮罩敏感信息：短于2字符显示 ****；<=8 字符显示前2位；否则显示前4位+后4位。"""
    n = len(secret)
    if n <= 2:
        return "****"
    if n <= 8:
        return f"{secret[:2]}****"
    return f"{secret[:4]}****{secret[-4:]}"


def _account_to_response(acc: AccountRecord) -> AccountResponse:
    """将 AccountRecord 转为 API 响应，apikey 解密后遮罩。"""
    try:
        plain = decrypt_secret(acc.apikey)
    except ValueError:
        plain = ""
    return AccountResponse(
        id=acc.id,
        name=acc.name,
        apikey_masked=_mask(plain),
        created_at=acc.created_at,
    )


# ---------------------------------------------------------------------------
# Pydantic 请求/响应模型
# ---------------------------------------------------------------------------


class AccountCreate(BaseModel):
    """创建账户请求体 — apikey 不能为空。"""

    name: str
    apikey: str = Field(..., min_length=1)


class AccountResponse(BaseModel):
    """账户响应 — apikey 仅展示遮罩后的值。"""

    id: int
    name: str
    apikey_masked: str
    created_at: str


class PasswordChange(BaseModel):
    """修改密码请求体。"""

    new_password: str


class SosTokenUpdate(BaseModel):
    """更新 SOS 令牌请求体。"""

    token: str


# ---------------------------------------------------------------------------
# 端点实现
# ---------------------------------------------------------------------------


@router.get("/api/settings")
async def get_settings(db: aiosqlite.Connection = Depends(get_db)) -> dict[str, Any]:
    """返回当前设置摘要：账户列表、SOS 令牌遮罩、是否有密码。"""
    pwd_hash = await get_setting(db, _KEY_PASSWORD_HASH)
    sos_encrypted = await get_setting(db, _KEY_SOS_TOKEN)

    # SOS 令牌解密并遮罩
    sos_masked = ""
    if sos_encrypted:
        try:
            sos_masked = _mask(decrypt_secret(sos_encrypted))
        except ValueError:
            sos_masked = "***"

    accounts = await list_accounts(db)
    return {
        "accounts": [_account_to_response(a) for a in accounts],
        "sos_token_masked": sos_masked,
        "has_password": pwd_hash is not None,
    }


@router.put("/api/settings/password")
async def set_password(
    body: PasswordChange,
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """设置或替换管理后台登录密码（sha256 哈希，与 login 端点一致）。"""
    token = base64.b64encode(
        hashlib.sha256(body.new_password.encode("utf-8")).digest()
    ).decode("ascii")
    await set_setting(db, _KEY_PASSWORD_HASH, token)
    # 同步更新内存中的 token，避免需要重启
    request.app.state.admin_token = token  # pyright: ignore[reportAny]
    return {"success": True, "message": "密码已设置"}


@router.put("/api/settings/sos-token")
async def set_sos_token(
    body: SosTokenUpdate,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """设置 SOS 令牌（加密存储）。"""
    await set_setting(db, _KEY_SOS_TOKEN, encrypt_secret(body.token))
    return {"success": True, "message": "SOS 令牌已设置"}


@router.get("/api/accounts", response_model=list[AccountResponse])
async def get_accounts(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[AccountResponse]:
    """列出所有账户，apikey 已解密并遮罩。"""
    accounts = await list_accounts(db)
    return [_account_to_response(a) for a in accounts]


@router.post("/api/accounts", response_model=AccountResponse)
async def create_account_route(
    body: AccountCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> AccountResponse:
    """创建新账户 — apikey 加密后存入数据库。

    422 响应：apikey 为空字符串时由 Pydantic min_length=1 校验触发。
    """
    record = await create_account(db, body.name, encrypt_secret(body.apikey))
    return _account_to_response(record)


@router.delete("/api/accounts/{account_id}")
async def delete_account_route(
    account_id: int,
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """删除账户 — 数据库 ON DELETE CASCADE 会自动删除关联的服务器记录。"""
    await delete_account(db, account_id)
    clear_client(account_id)
    return {"success": True, "message": f"账户 {account_id} 已删除"}
