"""products 路由 — 多地域产品列表与筛选。"""
from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from admin.api_routes.shared import get_client, get_db, run_async
from zhaomu.errors import AuthError, ZhaomuError

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
async def list_products(
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    region_ids: str = Query(..., description="逗号分隔的地域 ID 列表"),
    cpu: int | None = Query(None, description="CPU 核数精确匹配"),
    traffic: str | None = Query(None, description="流量筛选: unlimited/1000/2000"),
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取多地域产品列表，每个可用区独立一行，支持 CPU/流量筛选。"""
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None

    try:
        rid_list = [int(rid.strip()) for rid in region_ids.split(",") if rid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="region_ids 格式错误，需要逗号分隔的整数") from None

    if not rid_list:
        return []

    result_rows: list[dict[str, object]] = []

    for rid in rid_list:
        try:
            products = await run_async(client.product.list, rid)
        except AuthError:
            raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
        except ZhaomuError:
            continue

        for p in products:
            if p.outOfStock != 0:
                continue
            result_rows.append({
                "id": p.id,
                "cpu": p.cpu,
                "ram": p.ram,
                "disk": p.disk,
                "diskMax": p.diskMax,
                "traffic": p.traffic,
                "bandwidth": p.bandwidth,
                "diskMedia": p.diskMedia,
                "price": p.price,
                "priceQuarter": p.priceQuarter,
                "priceHalfYear": p.priceHalfYear,
                "priceYear": p.priceYear,
                "tags": p.tags,
                "zone": rid,
            })

    if cpu is not None:
        result_rows = [r for r in result_rows if r["cpu"] == cpu]

    if traffic is not None:
        if traffic == "unlimited":
            result_rows = [r for r in result_rows if r["traffic"] == 0]
        else:
            try:
                threshold = int(traffic)
                result_rows = [r for r in result_rows if r["traffic"] >= threshold or r["traffic"] == 0]
            except ValueError:
                pass

    result_rows.sort(key=lambda x: x["price"])  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
    return result_rows
