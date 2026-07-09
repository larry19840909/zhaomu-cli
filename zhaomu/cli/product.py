import re

import click

from zhaomu.cli import handle_api_errors, json_output, pass_client
from zhaomu.cli.resolvers import resolve_product, resolve_regions_by_city, filter_by_zone
from zhaomu.client import ZhaomuClient


@click.group()
def product():
    """Manage cloud server products."""


@product.command("list")
@click.option("-r", "--region", required=True, help="City name or region ID")
@click.option("--zone", default=None, help="Filter by zone code (e.g. V,R)")
@pass_client
@handle_api_errors
def product_list(client: ZhaomuClient, region, zone):
    """List products in a region (all zones if city name matches multiple)."""
    region_ids = filter_by_zone(client,
                                resolve_regions_by_city(client, region), zone)
    # 按 spec 去重，记录 zone 信息
    seen = {}  # key: (cpu, ram, disk, tags) → {"product": CloudProduct, "zones": set}
    for rid in region_ids:
        products = client.product.list(rid)
        for p in products:
            key = (p.cpu, p.ram, p.disk, p.tags)
            if key in seen:
                # 取价格最低的
                if p.price < seen[key]["product"].price:
                    seen[key] = {"product": p, "zones": seen[key]["zones"]}
                seen[key]["zones"].add(rid)
            else:
                seen[key] = {"product": p, "zones": {rid}}

    # 获取 zone 码映射
    zone_map = {r.id: r.zone for r in client.region.list()}

    # 按 zone（字母序）→ 价格（升序）排列
    items = sorted(seen.values(), key=lambda x: (
        min(zone_map.get(rid, str(rid)) for rid in x["zones"]),
        x["product"].price
    ))

    if json_output([{"id": item["product"].id, "cpu": item["product"].cpu,
                     "ram": item["product"].ram, "disk": item["product"].disk,
                     "price": item["product"].price, "traffic": item["product"].traffic,
                     "tags": item["product"].tags,
                     "zones": [zone_map.get(rid, str(rid)) for rid in sorted(item["zones"])]}
                    for item in items]):
        return

    header = f"{'ID':<6} {'CPU':<6} {'RAM':<8} {'Disk':<10} {'Traffic':<10} {'Monthly':<10} {'Zone':<8} {'Tags'}"
    click.echo(header)
    for item in items:
        p = item["product"]
        ram_label = f"{p.ram // 1024}G" if p.ram >= 1024 else f"{p.ram}M"
        zone_str = ",".join(sorted(zone_map.get(rid, str(rid)) for rid in item["zones"]))
        click.echo(f"{p.id:<6} {p.cpu:<6} {ram_label:<8} "
                   f"{f'{p.disk}G':<10} {f'{p.traffic}G':<10} "
                   f"{p.price:<10} {zone_str:<8} {p.tags}")


@product.command("info")
@click.argument("product_id")
@click.option("-r", "--region", default=None, help="City (for name resolution)")
@click.option("--zone", default=None, help="Zone filter when using city name")
@pass_client
@handle_api_errors
def product_info(client: ZhaomuClient, product_id, region, zone):
    """Show product details."""
    if product_id.isdigit():
        pid = int(product_id)
    elif region:
        rids = resolve_regions_by_city(client, region)
        rids = filter_by_zone(client, rids, zone)
        pid = resolve_product(client, rids[0], product_id)
    else:
        raise click.UsageError("use -r/--region to resolve product by name")
    result = client.product.info(pid)
    if json_output({"id": result.id, "cpu": result.cpu, "ram": result.ram, "disk": result.disk,
                    "traffic": result.traffic, "diskMedia": result.diskMedia,
                    "price": result.price, "priceHour": result.priceHour,
                    "priceQuarter": result.priceQuarter, "priceHalfYear": result.priceHalfYear,
                    "priceYear": result.priceYear, "tags": result.tags}):
        return
    ram_label = f"{result.ram // 1024}G" if result.ram >= 1024 else f"{result.ram}M"
    click.echo(f"ID:         {result.id}")
    click.echo(f"CPU:        {result.cpu} core(s)")
    click.echo(f"RAM:        {ram_label}")
    click.echo(f"Disk:       {result.disk}G {result.diskMedia}")
    click.echo(f"Traffic:    {result.traffic}G/mo")
    click.echo(f"Monthly:    {result.price}")
    click.echo(f"Quarterly:  {result.priceQuarter}")
    click.echo(f"Half-year:  {result.priceHalfYear}")
    click.echo(f"Yearly:     {result.priceYear}")
    if result.tags:
        click.echo(f"Tags:       {result.tags}")


@product.command("price")
@click.argument("product_id")
@click.option("-r", "--region", default=None, help="City (for name resolution)")
@click.option("--zone", default=None, help="Zone filter when using city name")
@pass_client
@handle_api_errors
def product_price(client: ZhaomuClient, product_id, region, zone):
    """Get product pricing."""
    if product_id.isdigit():
        pid = int(product_id)
    elif region:
        rids = resolve_regions_by_city(client, region)
        rids = filter_by_zone(client, rids, zone)
        pid = resolve_product(client, rids[0], product_id)
    else:
        raise click.UsageError("use -r/--region to resolve product by name")
    result = client.product.price(pid)
    if json_output(result):
        return
    cycle_names = {"1": "Monthly", "2": "Quarterly", "3": "Half-year", "4": "Yearly", "5": "Hourly"}
    for k, v in result.items():
        label = cycle_names.get(k, f"Cycle {k}")
        click.echo(f"{label:<12} {v}")


@product.command("compare")
@click.option("-r", "--region", required=True, help="City name or region ID")
@click.option("--zone", default=None, help="Filter by zone code (e.g. V,R)")
@pass_client
@handle_api_errors
def product_compare(client: ZhaomuClient, region, zone):
    """Compare product features across zones."""
    region_ids = filter_by_zone(client,
                                resolve_regions_by_city(client, region), zone)
    zone_map = {r.id: r.zone for r in client.region.list()}

    # 按 zone 逐一查询
    matrix: dict[str, dict[str, str]] = {}
    feature_order: list[str] = []
    for rid in region_ids:
        zone = zone_map.get(rid, str(rid))
        for item in client.product.compare(rid):
            if item.name not in matrix:
                matrix[item.name] = {}
                feature_order.append(item.name)
            matrix[item.name][zone] = item.explain

    # zone→id 反向映射（当前城市内唯一）
    zone_to_id = {}
    for rid in region_ids:
        zone_to_id[zone_map.get(rid, str(rid))] = rid

    sorted_zones = sorted(zone_to_id.keys())

    # 值缩写 + HTML 清理
    SHORT = {"支持": "是", "不支持": "否", "提交工单": "工单"}

    def _cell(v: str, w: int) -> str:
        v = SHORT.get(v, v)
        v = re.sub(r"<[^>]+>", " ", v)
        v = " ".join(v.split())
        if len(v) > w:
            v = v[:w - 2] + ".."
        return v

    if json_output({"zones": [{"zone": z, "id": zone_to_id[z]} for z in sorted_zones],
                    "features": [{"name": fn, **{z: matrix[fn].get(z, "") for z in sorted_zones}}
                                 for fn in feature_order]}):
        return

    # 表头标签: zone(id)
    zone_labels = [f"{z}({zone_to_id[z]})" for z in sorted_zones]

    # 计算列宽（每列独立）
    NAME_W = min(max(len(fn) for fn in feature_order) + 2, 24)
    ZONE_W = {}
    for i, z in enumerate(sorted_zones):
        raw_w = max((len(_cell(matrix[fn].get(z, "-"), 99)) for fn in feature_order), default=4)
        ZONE_W[z] = min(max(raw_w, len(zone_labels[i])) + 2, 18)

    # 表头
    header = f"{'Feature':<{NAME_W}}" + "".join(f"{zone_labels[i]:^{ZONE_W[z]}}" for i, z in enumerate(sorted_zones))
    click.echo(header)
    click.echo("-" * (NAME_W + sum(ZONE_W.values())))

    for fn in feature_order:
        row = f"{fn:<{NAME_W}}"
        for z in sorted_zones:
            val = _cell(matrix[fn].get(z, "-"), ZONE_W[z])
            row += f"{val:^{ZONE_W[z]}}"
        click.echo(row)
