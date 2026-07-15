"""servers 路由 — 云服务器管理，含 deploy/destroy 操作。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query

from admin.api_routes.shared import get_client, get_db, run_async
from admin.crypto import decrypt_secret
from admin.db import (
    get_server_record,
    get_setting,
    list_servers_by_account,
    ServerRecord,
    update_server_status,
)
from zhaomu.errors import ZhaomuError
from zhaomu_deploy.client import DeployClient, resolve_region_id
from zhaomu_deploy.models import DeployRequest, VpsLoginInfo

if TYPE_CHECKING:
    import aiosqlite

router = APIRouter(prefix="/api/servers", tags=["servers"])

# zhaomu 状态码 → 字符串映射
_STATUS_MAP: dict[int, str] = {
    1: "provisioning",
    2: "running",
    3: "stopped",
    4: "disabled",
    5: "preparing",
}


def _status_str(status: int) -> str:
    """将 zhaomu API 返回的状态码（int）转为字符串。"""
    return _STATUS_MAP.get(status, "unknown")


def _server_to_dict(rec: ServerRecord) -> dict[str, object]:
    """将 ServerRecord 转为 JSON 可序列化字典。"""
    return {
        "id": rec.id,
        "account_id": rec.account_id,
        "server_id": rec.server_id,
        "product_id": rec.product_id,
        "region_id": rec.region_id,
        "image": rec.image,
        "disk": rec.disk,
        "payment_cycle": rec.payment_cycle,
        "ip": rec.ip,
        "status": rec.status,
        "deployed_at": rec.deployed_at,
        "ordered_at": rec.ordered_at,
        "destroyed_at": rec.destroyed_at,
    }


async def _get_sos_token(db: aiosqlite.Connection) -> str:  # type: ignore[valid-type]
    """从 DB settings 读取并解密 SOS token，缺失时抛出 400。"""
    encrypted = await get_setting(db, "sos_token")
    if not encrypted:
        raise HTTPException(status_code=400, detail="SOS token not configured")
    try:
        return decrypt_secret(encrypted)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to decrypt SOS token: {e}"
        ) from e


# ---------------------------------------------------------------------------
# GET /api/servers — 列出服务器（含 live 状态富化）
# ---------------------------------------------------------------------------

@router.get("")
async def list_servers(
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]  # pyright: ignore[reportCallInDefaultInitializer]
):
    """列出指定账户下的所有云服务器，并用 zhaomu API 实时状态富化。

    Query params:
        account_id: 账户 ID
    """
    records = await list_servers_by_account(db, account_id)

    # 尝试从 zhaomu API 获取 live 状态
    live_map: dict[int, dict[str, object]] = {}
    try:
        client = await get_client(account_id, db)
        servers = await run_async(client.cloud.list)
        for s in servers:
            live_map[s.id] = {
                "live_status": _status_str(s.status),
                "live_ip": s.ip,
                "cpu": s.cpu,
                "ram": s.ram,
                "disk_system": s.disk,
                "image": s.image,
            }
    except (ZhaomuError, ValueError):
        pass  # API 不可用或账户不存在时静默降级

    result: list[dict[str, object]] = []
    for rec in records:
        entry = _server_to_dict(rec)
        entry["live"] = live_map.get(rec.server_id)
        result.append(entry)
    return result


# ---------------------------------------------------------------------------
# GET /api/servers/{server_db_id}/poll — 强制拉取实时状态
# ---------------------------------------------------------------------------

@router.get("/{server_db_id}/poll")
async def poll_server(
    server_db_id: int,
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]  # pyright: ignore[reportCallInDefaultInitializer]
):
    """强制轮询：调用 client.cloud.info() 获取最新状态并更新 DB。

    Path params:
        server_db_id: 服务器内部 DB ID
    Query params:
        account_id: 账户 ID
    """
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None
    try:
        detail = await run_async(client.cloud.info, rec.server_id)
    except ZhaomuError as e:
        raise HTTPException(
            status_code=502, detail=f"zhaomu cloud info API 出错：{e}"
        ) from e

    # 将状态码映射为字符串并更新 DB
    new_status = _status_str(detail.status)
    new_ip = detail.ip or ""
    await update_server_status(db, server_db_id, new_status, ip=new_ip)

    # 返回更新后的记录
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record disappeared after update")
    result = _server_to_dict(rec)
    result["live"] = {
        "live_status": new_status,
        "live_ip": new_ip,
        "cpu": detail.cpu,
        "ram": detail.ram,
        "disk_system": detail.disk,
        "image": detail.image,
    }
    return result


# ---------------------------------------------------------------------------
# POST /api/servers/{server_db_id}/deploy — 部署到 MetroVPN
# ---------------------------------------------------------------------------

@router.post("/{server_db_id}/deploy")
async def deploy_server(
    server_db_id: int,
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]  # pyright: ignore[reportCallInDefaultInitializer]
):
    """将已运行的云服务器部署到 MetroVPN 系统。

    Path params:
        server_db_id: 服务器内部 DB ID
    Query params:
        account_id: 账户 ID
    """
    # 1. 读取 DB 记录
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    # 2. 前置校验：状态和 IP
    if rec.status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"server is not running (current status: {rec.status})",
        )
    if not rec.ip:
        raise HTTPException(status_code=400, detail="server has no IP address")

    # 3. 获取 SOS token
    sos_token = await _get_sos_token(db)

    # 4. 获取 zhaomu 实例详情
    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None
    try:
        inst = await run_async(client.cloud.info, rec.server_id)
    except ZhaomuError as e:
        raise HTTPException(
            status_code=502, detail=f"zhaomu cloud info API 出错：{e}"
        ) from e

    # 5. 获取地域信息
    try:
        region = await run_async(client.region.info, rec.region_id)
    except ZhaomuError as e:
        raise HTTPException(
            status_code=502, detail=f"zhaomu region info API 出错：{e}"
        ) from e

    # 6. 解析 MetroVPN region_id
    city_name = region.cityEn or region.city
    try:
        deploy_region_id = resolve_region_id(city_name)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"无法解析地域 '{city_name}'：{e}"
        ) from e

    # 7. 构建 VpsLoginInfo 和 DeployRequest
    vps_info = VpsLoginInfo(
        vps_id=str(rec.server_id),
        password=inst.password,
        ip=inst.ip,
        os=(inst.image or "").lower(),
        vps_type=f"{inst.cpu}C-{inst.ram // 1024}G",
        user="root",
        port="22",
    )
    deploy_req = DeployRequest(
        region_id=deploy_region_id,
        vcpus=inst.cpu,
        memory=inst.ram,
        disk=inst.disk,
        vps_infos=[vps_info],
    )

    # 8. 调用 MetroVPN deploy API
    try:
        result = DeployClient(sos_token).create_deploy(deploy_req)
    except Exception:
        raise HTTPException(
            status_code=500, detail="MetroVPN deploy 内部错误，请检查 SOS Token 和网络连接"
        ) from None

    if result.code != 200:
        # deploy 失败，状态不变
        return {
            "success": False,
            "message": f"deploy failed: {result.msg}",
            "deploy_code": result.code,
            "server_ip": result.ip,
        }

    # 9. 更新 DB：标记为 deployed
    now = datetime.now(timezone.utc).isoformat()
    await update_server_status(db, server_db_id, "deployed", deployed_at=now)

    return {
        "success": True,
        "message": result.msg,
        "deploy_code": result.code,
        "server_ip": result.ip,
        "deployed_at": now,
    }


# ---------------------------------------------------------------------------
# DELETE /api/servers/{server_db_id} — 销毁云服务器
# ---------------------------------------------------------------------------

@router.delete("/{server_db_id}")
async def destroy_server(
    server_db_id: int,
    account_id: int = Query(...),  # pyright: ignore[reportCallInDefaultInitializer]
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]  # pyright: ignore[reportCallInDefaultInitializer]
):
    """销毁云服务器（调用 zhaomu API destroy + 更新 DB 状态）。

    Path params:
        server_db_id: 服务器内部 DB ID
    Query params:
        account_id: 账户 ID
    """
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    if rec.status == "destroyed":
        raise HTTPException(
            status_code=400, detail="server is already destroyed"
        )

    try:
        client = await get_client(account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {account_id} 不存在") from None
    try:
        _ = await run_async(client.cloud.destroy, rec.server_id)
    except ZhaomuError as e:
        raise HTTPException(
            status_code=502, detail=f"zhaomu cloud destroy API 出错：{e}"
        ) from e

    now = datetime.now(timezone.utc).isoformat()
    await update_server_status(db, server_db_id, "destroyed", destroyed_at=now)

    return {
        "success": True,
        "message": f"server {rec.server_id} destroyed",
        "destroyed_at": now,
    }
