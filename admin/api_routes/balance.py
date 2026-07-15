"""balance 路由 — 查询账户余额。"""
from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from admin.api_routes.shared import get_client, get_db, run_async
from zhaomu.errors import AuthError, ZhaomuError

router = APIRouter(prefix="/api", tags=["balance"])


@router.get("/balance")
async def get_balance(
    account_id: int = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None
    try:
        result = await run_async(client.other.balance)
    except AuthError:
        raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu 余额 API 出错: {e}") from e
    return {"balance": result.balance}
