import re
from typing import Any, Callable, List, TypeVar

import click

from zhaomu.client import ZhaomuClient

T = TypeVar("T")


def _looks_like_ip(value: str) -> bool:
    return bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value.strip()))


def resolve_by_ip(client: ZhaomuClient, list_fn: Callable[[], List[Any]], value: str) -> int:
    """通过 IP 地址解析实例 ID。value 可能已经是纯数字 ID。"""
    v = value.strip()
    if not v:
        raise click.UsageError("instance identifier cannot be empty")
    if v.isdigit():
        return int(v)
    if _looks_like_ip(v):
        items = list_fn()
        for item in items:
            if item.ip == v:
                return item.id
        raise click.UsageError(f"no instance found with IP {v}")
    raise click.UsageError(f"invalid instance identifier: {v}")


def resolve_region(client: ZhaomuClient, value: str) -> int:
    """通过城市名（中/英）或裸 ID 解析可用区编号（返回第一个匹配项）。"""
    results = resolve_regions_by_city(client, value)
    return results[0]


def resolve_regions_by_city(client: ZhaomuClient, value: str) -> List[int]:
    """通过城市名（中/英）或裸 ID 解析该城市下所有可用区编号。"""
    v = value.strip()
    if not v:
        raise click.UsageError("region cannot be empty")
    if v.isdigit():
        return [int(v)]
    v_lower = v.lower()
    regions = client.region.list()
    # 精确 city/cityEn 匹配优先
    exact = [r.id for r in regions
             if (r.cityEn or "").lower() == v_lower
             or (r.city or "").lower() == v_lower]
    if exact:
        return exact
    # 子串匹配回退
    matches = [r.id for r in regions
               if v_lower in (r.cityEn or "").lower()
               or v_lower in (r.city or "").lower()]
    if matches:
        return matches
    # 国家/区域匹配
    area_matches = [r.id for r in regions
                    if v_lower in (r.countryEn or "").lower()
                    or v_lower in (r.country or "").lower()
                    or v_lower in (r.areaEn or "").lower()
                    or v_lower in (r.area or "").lower()]
    if area_matches:
        return area_matches
    raise click.UsageError(f"no region found matching: {v}")


def filter_by_zone(client: ZhaomuClient, region_ids: List[int], zone_value: str | None) -> List[int]:
    """在 region_ids 中按 zone 码筛选。支持逗号分隔列表（如 V,R）。"""
    if not zone_value:
        return region_ids
    zone_map = {r.id: r.zone for r in client.region.list()}
    targets = [t.strip() for t in zone_value.split(",") if t.strip()]
    result: List[int] = []
    for target in targets:
        if target.isdigit():
            tid = int(target)
            if tid not in region_ids:
                raise click.UsageError(f"region ID {tid} not in the selected city")
            result.append(tid)
        else:
            found = [rid for rid in region_ids if zone_map.get(rid, "") == target]
            if not found:
                available = ", ".join(zone_map.get(rid, str(rid)) for rid in region_ids)
                raise click.UsageError(f"zone '{target}' not found. Available: {available}")
            result.extend(found)
    return result


def resolve_product(client: ZhaomuClient, region_id: int, value: str) -> int:
    """通过 CPU/RAM 组合标识（如 '1C-1G'）或裸 ID 解析产品编号。"""
    v = value.strip()
    if not v:
        raise click.UsageError("product cannot be empty")
    if v.isdigit():
        return int(v)
    v_lower = v.lower()
    products = client.product.list(region_id)
    for p in products:
        ram_gb = p.ram // 1024 if p.ram >= 1024 else p.ram
        ram_suffix = "G" if p.ram >= 1024 else "M"
        label = f"{p.cpu}c-{ram_gb}{ram_suffix}".lower()
        if label == v_lower:
            return p.id
    raise click.UsageError(f"no product found matching: {v}")


def resolve_image(client: ZhaomuClient, product_id: int, value: str) -> int:
    """通过镜像名或裸 ID 解析镜像编号。"""
    v = value.strip()
    if not v:
        raise click.UsageError("image cannot be empty")
    if v.isdigit():
        return int(v)
    v_lower = v.lower()
    images = client.cloud.images(product_id)
    # 精确匹配优先
    for img in images:
        if img.name.lower() == v_lower:
            return img.id
    # 子串匹配回退
    for img in images:
        if v_lower in img.name.lower():
            return img.id
    raise click.UsageError(f"no image found matching: {v}")
