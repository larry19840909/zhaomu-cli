"""admin/scripts/backfill_data.py — 回填服务器缺失数据。

从 zhaomu API 拉取 country, city, ip_type, root, password, cpu, ram,
diskData, diskMedia, traffic, startTime, endTime, isAutoRenew 等字段，
更新到本地 admin DB 中。跳过已销毁的服务器。
"""

import asyncio
import sys
from pathlib import Path

import aiosqlite

# 确保项目根目录在 sys.path 中，以便导入 zhaomu 和 admin 模块
_project_root = Path(__file__).resolve().parent.parent.parent  # admin/scripts/ -> admin/ -> .
sys.path.insert(0, str(_project_root))

from admin.crypto import decrypt_secret  # noqa: E402
from zhaomu.client import ZhaomuClient  # noqa: E402
from zhaomu.errors import ZhaomuError  # noqa: E402


# 数据库路径相对于项目根目录
DB_PATH = _project_root / "admin.db"


async def main() -> None:
    db = await aiosqlite.connect(str(DB_PATH))
    db.row_factory = aiosqlite.Row

    # 1. 加载所有账户的 API Key
    acc_cursor = await db.execute("SELECT id, apikey FROM accounts")
    acc_rows = await acc_cursor.fetchall()
    acc_map: dict[int, str] = {}
    for r in acc_rows:
        try:
            acc_map[r["id"]] = decrypt_secret(r["apikey"])
        except Exception as exc:
            print(f"[WARN] 账户 {r['id']} 解密 apikey 失败: {exc}")

    print(f"已加载 {len(acc_map)} 个账户")

    # 2. 查询需要回填的服务器
    srv_cursor = await db.execute(
        "SELECT * FROM servers WHERE status != '已销毁'"
    )
    servers = await srv_cursor.fetchall()
    print(f"共 {len(servers)} 个未销毁服务器需要处理\n")

    ok_count = 0
    fail_count = 0

    for srv in servers:
        server_db_id: int = srv["id"]
        server_id: int = srv["server_id"]
        product_id: int = srv["product_id"]
        region_id: int = srv["region_id"]
        account_id: int = srv["account_id"]

        apikey = acc_map.get(account_id)
        if not apikey:
            print(f"[SKIP] server {server_id}: 找不到账户 {account_id} 的 API Key")
            fail_count += 1
            continue

        client = ZhaomuClient(apikey)
        label = f"server {server_id}"

        try:
            # 3a. 获取地域信息 → country, city
            region = await asyncio.to_thread(client.region.info, region_id)
            country = region.country or ""
            city = region.city or ""

            # 3b. 获取服务器详情
            detail = await asyncio.to_thread(client.cloud.info, server_id)
            root = detail.root or ""
            password = detail.password or ""
            cpu = detail.cpu
            ram = detail.ram
            disk_data = detail.diskData
            disk_media = detail.diskMedia or ""
            traffic = detail.traffic
            start_time = detail.startTime or ""
            end_time = detail.endTime or ""
            is_auto_renew = detail.isAutoRenew

            # 3c. 获取 IP 类型 — 从 product.info 的 tags 中提取
            ip_type = ""
            try:
                product = await asyncio.to_thread(client.product.info, product_id)
                tags = getattr(product, "tags", "") or ""
                if "原生IP" in tags:
                    ip_type = "原生IP"
                elif "住宅IP" in tags:
                    ip_type = "住宅IP"
            except ZhaomuError as exc:
                print(f"  [WARN] {label}: product.info API 失败 ({exc}), ip_type 留空")

            # 4. 更新数据库
            await db.execute(
                """UPDATE servers
                   SET country = ?, city = ?, ip_type = ?,
                       root = ?, password = ?, cpu = ?, ram = ?,
                       diskData = ?, diskMedia = ?, traffic = ?,
                       startTime = ?, endTime = ?, isAutoRenew = ?
                   WHERE id = ?""",
                (
                    country, city, ip_type,
                    root, password, cpu, ram,
                    disk_data, disk_media, traffic,
                    start_time, end_time, is_auto_renew,
                    server_db_id,
                ),
            )
            await db.commit()

            ok_count += 1
            print(
                f"[OK] {label}: country={country} city={city} ip_type={ip_type} "
                f"cpu={cpu} ram={ram} disk={disk_data}G({disk_media}) "
                f"traffic={traffic}G root={root}"
            )

        except ZhaomuError as exc:
            print(f"[FAIL] {label}: API 错误 — {exc}")
            fail_count += 1
        except Exception as exc:
            print(f"[FAIL] {label}: 未知错误 — {type(exc).__name__}: {exc}")
            fail_count += 1

    await db.close()
    print(f"\n=== 回填完成: 成功 {ok_count}, 失败 {fail_count} ===")


if __name__ == "__main__":
    asyncio.run(main())
