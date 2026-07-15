"""orders 路由 — 两阶段下单流程：prepare（查询镜像）→ order（提交订单）。"""
from __future__ import annotations

import aiosqlite
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from admin.api_routes.shared import get_client, get_db, run_async
from admin.db import create_server_record
from zhaomu.errors import APIError, AuthError, ZhaomuError
from zhaomu.models.cloud.request import OrderRequest

router = APIRouter(prefix="/api/orders", tags=["orders"])


class OrderItem(BaseModel):
    """单条下单请求项。"""

    product_id: int
    image_id: int
    disk: int = 0
    payment_cycle: int = 1
    quantity: int = Field(default=1, ge=1, le=10)


@router.get("/prepare/{product_id}")
async def prepare_order(
    product_id: int,
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """查询产品的可用镜像和配置信息，为下单做准备。"""
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None

    try:
        product = await run_async(client.product.info, product_id)
        images = await run_async(client.cloud.images, product_id)
    except AuthError:
        raise HTTPException(status_code=401, detail="API Key 无效，请检查账户设置") from None
    except APIError as e:
        raise HTTPException(status_code=400, detail=f"产品不存在或查询失败: {e}") from e
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu API 出错: {e}") from e

    return {
        "product": {
            "id": product.id,
            "cpu": product.cpu,
            "ram": product.ram,
            "disk": product.disk,
            "diskMax": product.diskMax,
            "diskData": product.diskData,
            "diskDataMax": product.diskDataMax,
            "diskMedia": product.diskMedia,
            "bandwidth": product.bandwidth,
            "bandwidthMax": product.bandwidthMax,
            "traffic": product.traffic,
            "priceHour": product.priceHour,
            "price": product.price,
            "priceQuarter": product.priceQuarter,
            "priceHalfYear": product.priceHalfYear,
            "priceYear": product.priceYear,
            "tags": product.tags,
            "outOfStock": product.outOfStock,
            "noWindows": product.noWindows,
            "region_id": product.region_id,
            "minPaymentCycle": product.minPaymentCycle,
        },
        "images": [
            {"id": img.id, "name": img.name, "type": img.type} for img in images
        ],
        "defaultImageId": images[0].id if images else 0,
        "minPaymentCycle": product.minPaymentCycle,
        "defaultDisk": product.disk,
        "diskMax": product.diskMax,
    }


@router.post("")
async def create_orders(
    orders: list[OrderItem],
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),
) -> dict[str, Any]:
    """批量提交云服务器订单。

    对每个订单项按 quantity 展开，每个子订单独立处理。
    认证失败不再丢弃已成功的结果，返回部分成功信息。
    """
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None

    results: list[dict[str, Any]] = []
    success_count = 0

    for item in orders:
        for _ in range(max(1, item.quantity)):
            # -- 获取产品信息 ---------------------------------------------
            try:
                product = await run_async(client.product.info, item.product_id)
            except APIError as e:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"产品 {item.product_id} 查询失败: {e}",
                })
                continue
            except ZhaomuError as e:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"查询产品 {item.product_id} 出错: {e}",
                })
                continue

            # -- 验证参数 ------------------------------------------------
            if item.payment_cycle < product.minPaymentCycle:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": (
                        f"产品 {item.product_id} 最低支付周期为 "
                        f"{product.minPaymentCycle}，当前为 {item.payment_cycle}"
                    ),
                })
                continue

            if item.payment_cycle < 1 or item.payment_cycle > 5:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"支付周期 {item.payment_cycle} 无效（范围 1-5）",
                })
                continue

            if item.disk < product.disk or item.disk > product.diskMax:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"磁盘 {item.disk}G 超出范围 [{product.disk}, {product.diskMax}]",
                })
                continue

            # -- 调用 zhaomu API 下单 ------------------------------------
            try:
                req = OrderRequest(
                    regionId=product.region_id,
                    productId=item.product_id,
                    disk=item.disk,
                    imageId=item.image_id,
                    paymentCycle=item.payment_cycle,
                )
                op_result = await run_async(client.cloud.order, req)
            except AuthError as e:
                # 认证失败 — 返回部分结果，不再丢弃已成功的服务器
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"认证失败（后续订单未执行）: {e}",
                })
                return JSONResponse(
                    status_code=401,
                    content={"success_count": success_count, "results": results, "aborted": True},
                )
            except ZhaomuError as e:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": f"下单失败: {e}",
                })
                continue

            # -- 处理下单结果 ---------------------------------------------
            if op_result.success and op_result.info:
                server_id_raw = op_result.info.get("id", 0)
                server_id = int(server_id_raw) if server_id_raw else 0

                _ = await create_server_record(
                    db,
                    account_id=account_id,
                    server_id=server_id,
                    product_id=item.product_id,
                    region_id=product.region_id,
                    image=str(item.image_id),
                    disk=item.disk,
                    payment_cycle=item.payment_cycle,
                    status="provisioning",
                )

                results.append({
                    "server_id": server_id,
                    "success": True,
                    "message": op_result.message,
                })
                success_count += 1
            else:
                results.append({
                    "server_id": 0,
                    "success": False,
                    "message": op_result.message or "下单失败",
                })

    return {"success_count": success_count, "results": results}
