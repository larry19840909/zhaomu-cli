"""filter 路由 — deploy 支持的 region 筛选和产品对比。"""
from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from admin.api_routes.shared import get_client, get_db, run_async
from zhaomu.errors import AuthError, ZhaomuError

# 尝试导入 _REGION_LOOKUP，不可用时降级为空字典
try:
    from zhaomu_deploy.client import _REGION_LOOKUP  # pyright: ignore[reportPrivateUsage]
except ImportError:
    _REGION_LOOKUP: dict[str, str] = {}  # pyright: ignore[reportConstantRedefinition]

router = APIRouter(prefix="/api/filter", tags=["filter"])

# target_id 27 = IP 类型（原生IP/住宅IP），来自 zhaomu compare API
_TARGET_ID_IP_TYPE = 27


def _classify(name: str, target_id: int) -> str:
    """根据 CompareItem 的 name/target_id 返回语义分类标签。"""
    name_lower = name.lower()
    if "ip" in name_lower or target_id == _TARGET_ID_IP_TYPE:
        return "ip_type"
    if any(kw in name_lower for kw in ("销毁", "退款", "refund", "destroy")):
        return "refund"
    return "other"


@router.get("/regions")
async def get_regions(
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取 deploy 支持的地域列表。"""
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None

    try:
        all_regions = await run_async(client.region.list)
    except AuthError:
        raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu 地域 API 出错：{e}") from e

    result: list[dict[str, object]] = []
    for r in all_regions:
        if r.city in _REGION_LOOKUP or r.cityEn in _REGION_LOOKUP:
            result.append({
                "id": r.id,
                "city": r.city,
                "zone": r.zone,
                "country": r.country,
            })
    return result


@router.get("/regions/{region_id}/compare")
async def get_compare(
    region_id: int,
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),
):
    """获取指定地域的产品对比信息。"""
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None

    try:
        compare_items = await run_async(client.product.compare, region_id)
    except AuthError:
        raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"产品对比 API 出错：{e}") from e

    features: list[dict[str, str]] = []
    has_refund = False
    for item in compare_items:
        category = _classify(item.name, item.target_id)
        features.append({
            "category": category,
            "name": item.name,
            "explanation": item.explain,
        })
        if category == "refund":
            # explain 为"支持"/"是"才表示该可用区支持销毁退款（排除"不支持"）
            if item.explain in ("支持", "是"):
                has_refund = True

    region_info: dict[str, object]
    try:
        region = await run_async(client.region.info, region_id)
        region_info = {"id": region.id, "city": region.city, "zone": region.zone}
    except ZhaomuError:
        region_info = {"id": region_id, "city": "", "zone": ""}

    return {"features": features, "has_refund": has_refund, "region_info": region_info}
