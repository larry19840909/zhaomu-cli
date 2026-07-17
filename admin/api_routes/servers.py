"""servers 路由 — 云服务器管理，含 deploy/destroy/batches 操作。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from admin.api_routes.shared import get_client, get_db, run_async
from admin.crypto import decrypt_secret
from admin.db import (
    get_server_record,
    get_setting,
    list_batches,
    list_servers_all,
    list_servers_by_account,
    ServerRecord,
    update_server_status,
)
from zhaomu.errors import APIError, ZhaomuError
from zhaomu_deploy.client import DeployClient, resolve_region_id
from zhaomu_deploy.models import DeployRequest, VpsLoginInfo

if TYPE_CHECKING:
    import aiosqlite

router = APIRouter(prefix="/api/servers", tags=["servers"])

_STATUS_LABELS: dict[int, str] = {
    2: "运行中",
    9: "销毁中",  # zhaomu 销毁过程中返回 9
}


def _status_str(status: int) -> str:
    """仅 2=运行中，其余透传。"""
    return _STATUS_LABELS.get(status, str(status))


def _get_field(rec: Any, field: str) -> str:
    """从 ServerRecord 或 dict 中取字段值（用于过滤）。"""
    if isinstance(rec, ServerRecord):
        return str(getattr(rec, field, ""))
    if isinstance(rec, dict):
        return str(rec.get(field, ""))
    return ""


def _apply_filters(
    records: list[Any],
    account_name: str | None,
    country: str | None,
    city: str | None,
    os_filter: str | None,
    has_refund: str | None,
    ip_type: str | None,
    deploy_status: str | None,
) -> list[Any]:
    """在内存中按 AND 逻辑过滤记录。每个参数支持逗号分隔的多值。"""
    filters: dict[str, set[str]] = {}
    if account_name:
        filters["account_name"] = set(account_name.split(","))
    if country:
        filters["country"] = set(country.split(","))
    if city:
        filters["city"] = set(city.split(","))
    if os_filter:
        filters["os"] = set(os_filter.split(","))
    if has_refund:
        filters["has_refund"] = set(has_refund.split(","))
    if ip_type:
        filters["ip_type"] = set(ip_type.split(","))
    if deploy_status:
        filters["deploy_status"] = set(deploy_status.split(","))

    if not filters:
        return records

    result: list[Any] = []
    for rec in records:
        matches = True
        for key, allowed in filters.items():
            if key == "os":
                val = _get_field(rec, "image")
            else:
                val = _get_field(rec, key)
            if val not in allowed:
                matches = False
                break
        if matches:
            result.append(rec)
    return result


def _server_to_dict(rec: ServerRecord, account_name: str = "") -> dict[str, object]:
    result: dict[str, object] = {
        "id": rec.id,
        "account_id": rec.account_id,
        "account_name": account_name,
        "server_id": rec.server_id,
        "product_id": rec.product_id,
        "region_id": rec.region_id,
        "batch_id": rec.batch_id,
        "image": rec.image,
        "disk": rec.disk,
        "payment_cycle": rec.payment_cycle,
        "ip": rec.ip,
        "status": rec.status,
        "deploy_status": rec.deploy_status,
        "deployed_at": rec.deployed_at,
        "ordered_at": rec.ordered_at,
        "destroyed_at": rec.destroyed_at,
        "has_refund": rec.has_refund,
        "country": rec.country,
        "city": rec.city,
        "ip_type": rec.ip_type,
        "root": rec.root,
        "cpu": rec.cpu,
        "ram": rec.ram,
        "diskData": rec.diskData,
        "diskMedia": rec.diskMedia,
        "traffic": rec.traffic,
        "startTime": rec.startTime,
        "endTime": rec.endTime,
        "isAutoRenew": rec.isAutoRenew,
    }
    return result


async def _get_sos_token(db: aiosqlite.Connection) -> str:  # type: ignore[valid-type]
    encrypted = await get_setting(db, "sos_token")
    if not encrypted:
        raise HTTPException(status_code=400, detail="SOS token not configured")
    try:
        return decrypt_secret(encrypted)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to decrypt SOS token: {e}"
        ) from e


async def _get_account_name(db: aiosqlite.Connection, account_id: int) -> str:  # type: ignore[valid-type]
    """查询账户名称。"""
    rows = list(await db.execute_fetchall(
        "SELECT name FROM accounts WHERE id = ?", (account_id,),
    ))
    return rows[0]["name"] if rows else ""  # pyright: ignore[reportAny]


# ---------------------------------------------------------------------------
# GET /api/servers — 列出全部服务器（可选按账户筛选）
# ---------------------------------------------------------------------------

@router.get("")
async def list_servers(
    account_id: int | None = Query(None),
    account_name: str | None = Query(None),
    country: str | None = Query(None),
    city: str | None = Query(None),
    os: str | None = Query(None),
    has_refund: str | None = Query(None),
    ip_type: str | None = Query(None),
    deploy_status: str | None = Query(None),
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """列出云服务器。不传 account_id 时返回全部服务器并附账户名。

    Query params:
        account_id: 可选，筛选指定账户
        account_name: 可选，按账户名筛选（逗号分隔多值）
        country: 可选，按国家筛选（逗号分隔多值）
        city: 可选，按城市筛选（逗号分隔多值）
        os: 可选，按系统镜像筛选（逗号分隔多值）
        has_refund: 可选，按退款状态筛选（逗号分隔多值）
        ip_type: 可选，按 IP 类型筛选（逗号分隔多值）
        deploy_status: 可选，按部署状态筛选（逗号分隔多值）
    """
    if account_id is not None:
        recs = await list_servers_by_account(db, account_id)
        account_name_val = await _get_account_name(db, account_id)
        # 应用内存过滤（AND 逻辑，逗号分隔多值）
        filtered = _apply_filters(
            list(recs), account_name, country, city, os, has_refund, ip_type, deploy_status,
        )
        # 尝试 live 状态富化
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
            pass
        return [
            {**_server_to_dict(rec, account_name_val), "live": live_map.get(rec.server_id)}  # type: ignore[arg-type,attr-defined]
            for rec in filtered
        ]

    # 返回全部服务器，按账户分组做 live 富化
    all_recs = await list_servers_all(db)
    # 应用内存过滤
    records_all = _apply_filters(
        list(all_recs),
        account_name, country, city, os, has_refund, ip_type, deploy_status,
    )
    # 按 account_id 分组
    by_account: dict[int, list[dict[str, object]]] = {}
    for r in records_all:
        aid: int = r["account_id"]  # type: ignore[assignment]
        if aid not in by_account:
            by_account[aid] = []
        by_account[aid].append(r)

    live_map: dict[int, dict[str, object]] = {}
    for aid, recs in by_account.items():
        # 调用 zhaomu API 获取当前状态
        try:
            client = await get_client(aid, db)
            servers = await run_async(client.cloud.list)
        except (ZhaomuError, ValueError):
            continue

        for s in servers:
            live_map[s.id] = {
                "live_status": _status_str(s.status),
                "live_ip": s.ip,
                "cpu": s.cpu, "ram": s.ram,
                "disk_system": s.disk, "image": s.image,
            }
            # 更新 DB 中状态变化的服务器
            new_status = _status_str(s.status)
            for rec in recs:
                if rec["server_id"] == s.id and rec.get("status") != new_status:
                    await update_server_status(db, rec["id"], new_status, ip=s.ip or "")  # pyright: ignore[reportArgumentType]
                    rec["status"] = new_status
                    rec["ip"] = s.ip or ""

    return [  # type: ignore[return-value]
        {
            "id": r["id"], "account_id": r["account_id"],
            "account_name": r.get("account_name", ""),
            "server_id": r["server_id"], "product_id": r["product_id"],
            "region_id": r["region_id"], "batch_id": r.get("batch_id", ""),
            "image": r.get("image", ""), "disk": r.get("disk", 0),
            "payment_cycle": r.get("payment_cycle", 0), "ip": r.get("ip", ""),
            "status": r.get("status", "—"),
            "deploy_status": r.get("deploy_status", ""),
            "deployed_at": r.get("deployed_at", ""), "ordered_at": r.get("ordered_at", ""),
            "destroyed_at": r.get("destroyed_at", ""),
            "has_refund": r.get("has_refund", 0),
            "country": r.get("country", ""),
            "city": r.get("city", ""),
            "ip_type": r.get("ip_type", ""),
            "root": r.get("root", ""),
            "cpu": r.get("cpu", 0),
            "ram": r.get("ram", 0),
            "diskData": r.get("diskData", 0),
            "diskMedia": r.get("diskMedia", ""),
            "traffic": r.get("traffic", 0),
            "startTime": r.get("startTime", ""),
            "endTime": r.get("endTime", ""),
            "isAutoRenew": r.get("isAutoRenew", 0),
            "live": live_map.get(r["server_id"]),  # type: ignore[arg-type]
        }
        for r in records_all
    ]


# ---------------------------------------------------------------------------
# GET /api/servers/{server_db_id}/poll — 用服务器自己的 account_id 拉状态
# ---------------------------------------------------------------------------

@router.get("/{server_db_id}/poll")
async def poll_server(
    server_db_id: int,
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """强制轮询：用服务器所属账户的 API Key 拉取最新状态。"""
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    try:
        client = await get_client(rec.account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {rec.account_id} 不存在") from None
    try:
        detail = await run_async(client.cloud.info, rec.server_id)
    except APIError as e:
        # 404 表示服务器已在 zhaomu 端被删除，自动标记为已销毁
        if "not found" in str(e).lower() or "404" in str(e):
            now = datetime.now(timezone.utc).isoformat()
            await update_server_status(db, server_db_id, "已销毁", destroyed_at=now)
            return {"status": "已销毁", "message": "服务器已不存在（已自动标记为已销毁）", "destroyed_at": now}
        raise HTTPException(status_code=502, detail=f"zhaomu cloud info API 出错：{e}") from e
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu cloud info API 出错：{e}") from e

    new_status = _status_str(detail.status)
    new_ip = detail.ip or ""
    await update_server_status(db, server_db_id, new_status, ip=new_ip)

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
# GET /api/servers/{server_db_id}/detail — 获取服务器详情（代理 cloud.info）
# ---------------------------------------------------------------------------

@router.get("/{server_db_id}/detail")
async def get_server_detail(
    server_db_id: int,
    force: bool = Query(False),
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """获取服务器详细信息，代理 zhaomu cloud.info API 并缓存到 DB。

    首次调用时从 zhaomu API 拉取详情并写入 servers 表列；
    后续调用直接返回 DB 缓存。force=True 强制重新拉取。
    密码在响应中始终掩码为 **。
    """
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    # 如果 force 或密码为空，从 zhaomu API 拉取详情
    if force or not rec.password:
        try:
            client = await get_client(rec.account_id, db)
        except ValueError:
            raise HTTPException(status_code=404, detail=f"账户 {rec.account_id} 不存在") from None
        try:
            detail = await run_async(client.cloud.info, rec.server_id)
        except ZhaomuError as e:
            raise HTTPException(status_code=502, detail=f"zhaomu cloud info API 出错：{e}") from e

        # 尝试获取地域信息补充 country/city
        country_val = rec.country
        city_val = rec.city
        if not country_val or not city_val:
            try:
                region = await run_async(client.region.info, rec.region_id)
                if not country_val:
                    country_val = getattr(region, "country", "") or ""
                if not city_val:
                    city_val = getattr(region, "city", "") or ""
            except ZhaomuError:
                pass  # 地域 API 不可用时静默降级

        # 将详情更新到 DB
        await db.execute(
            """UPDATE servers SET
               root = ?, password = ?, cpu = ?, ram = ?,
               diskData = ?, diskMedia = ?, traffic = ?,
               startTime = ?, endTime = ?, isAutoRenew = ?,
               country = CASE WHEN country = '' OR country IS NULL THEN ? ELSE country END,
               city = CASE WHEN city = '' OR city IS NULL THEN ? ELSE city END
               WHERE id = ?""",
            (
                getattr(detail, "root", "") or "",
                getattr(detail, "password", "") or "",
                getattr(detail, "cpu", 0) or 0,
                getattr(detail, "ram", 0) or 0,
                getattr(detail, "diskData", 0) or 0,
                getattr(detail, "diskMedia", "") or "",
                getattr(detail, "traffic", 0) or 0,
                getattr(detail, "startTime", "") or "",
                getattr(detail, "endTime", "") or "",
                getattr(detail, "isAutoRenew", 0) or 0,
                country_val,
                city_val,
                server_db_id,
            ),
        )
        await db.commit()
        # 重新读取更新后的记录
        rec = await get_server_record(db, server_db_id)
        if rec is None:
            raise HTTPException(status_code=404, detail="server record disappeared after update")

    # 构建响应，密码掩码
    result = _server_to_dict(rec)
    result["password"] = "**"
    result["password_raw"] = rec.password or ""
    result["ordered_at"] = rec.ordered_at
    return result


# ---------------------------------------------------------------------------
# POST /api/servers/{server_db_id}/deploy — 用服务器自己的 account_id
# ---------------------------------------------------------------------------

@router.post("/{server_db_id}/deploy")
async def deploy_server(
    server_db_id: int,
    group_id: str = Query("HighSpeed Server"),
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """部署到 MetroVPN，用服务器所属账户获取实例详情。"""
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    if rec.status != "运行中":
        raise HTTPException(status_code=400, detail="仅运行中的服务器可以部署")
    if not rec.ip:
        raise HTTPException(status_code=400, detail="server has no IP address")

    sos_token = await _get_sos_token(db)

    try:
        client = await get_client(rec.account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {rec.account_id} 不存在") from None
    try:
        inst = await run_async(client.cloud.info, rec.server_id)
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu cloud info API 出错：{e}") from e

    try:
        region = await run_async(client.region.info, rec.region_id)
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu region info API 出错：{e}") from e

    city_name = region.cityEn or region.city
    try:
        deploy_region_id = resolve_region_id(city_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无法解析地域 '{city_name}'：{e}") from e

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
        group_id=group_id,
    )

    try:
        result = DeployClient(sos_token).create_deploy(deploy_req)
    except Exception:
        raise HTTPException(status_code=500, detail="MetroVPN deploy 内部错误，请检查 SOS Token 和网络连接") from None

    if result.code != 200:
        return {"success": False, "message": f"deploy failed: {result.msg}", "deploy_code": result.code, "server_ip": result.ip}

    now = datetime.now(timezone.utc).isoformat()
    await update_server_status(db, server_db_id, rec.status, deploy_status="已部署", deployed_at=now)
    return {"success": True, "message": result.msg, "deploy_code": result.code, "server_ip": result.ip, "deployed_at": now}


# ---------------------------------------------------------------------------
# DELETE /api/servers/{server_db_id} — 用服务器自己的 account_id
# ---------------------------------------------------------------------------

@router.delete("/{server_db_id}")
async def destroy_server(
    server_db_id: int,
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """销毁云服务器，用服务器所属账户的 API Key。"""
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    if rec.status == "已销毁":
        raise HTTPException(status_code=400, detail="server is already destroyed")

    try:
        client = await get_client(rec.account_id, db)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"账户 {rec.account_id} 不存在") from None
    try:
        _ = await run_async(client.cloud.destroy, rec.server_id)
    except ZhaomuError as e:
        raise HTTPException(status_code=502, detail=f"zhaomu cloud destroy API 出错：{e}") from e

    now = datetime.now(timezone.utc).isoformat()
    await update_server_status(db, server_db_id, "已销毁", destroyed_at=now)
    return {"success": True, "message": f"server {rec.server_id} destroyed", "destroyed_at": now}


# ---------------------------------------------------------------------------
# DELETE /api/servers/{server_db_id}/record — 硬删除服务器记录
# ---------------------------------------------------------------------------

@router.delete("/{server_db_id}/record")
async def delete_server_record(
    server_db_id: int,
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """硬删除服务器记录（仅限状态为"已销毁"的服务器）。

    Path params:
        server_db_id: 服务器内部 DB ID
    """
    rec = await get_server_record(db, server_db_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="server record not found")

    if rec.status != "已销毁":
        raise HTTPException(
            status_code=400, detail="仅已销毁的服务器可以删除记录"
        )

    await db.execute("DELETE FROM servers WHERE id = ?", (server_db_id,))
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# GET /api/batches — 批次列表
# ---------------------------------------------------------------------------

@router.get("/batches")
async def get_batches(
    db: aiosqlite.Connection = Depends(get_db),  # type: ignore[valid-type]
):
    """列出所有下单批次，含每批的服务器数量和状态分布。"""
    return await list_batches(db)
