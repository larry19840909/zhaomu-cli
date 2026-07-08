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
    """通过 city_code、城市名（中/英）或裸 ID 解析可用区编号。"""
    v = value.strip()
    if not v:
        raise click.UsageError("region cannot be empty")
    if v.isdigit():
        return int(v)
    v_lower = v.lower()
    regions = client.region.list()
    # 精确匹配优先
    for r in regions:
        if (r.cityEn or "").lower() == v_lower:
            return r.id
        if (r.city or "").lower() == v_lower:
            return r.id
    # 子串匹配回退
    for r in regions:
        if v_lower in (r.cityEn or "").lower():
            return r.id
        if v_lower in (r.city or "").lower():
            return r.id
        if v_lower in (r.countryEn or "").lower():
            return r.id
        if v_lower in (r.country or "").lower():
            return r.id
        if v_lower in (r.areaEn or "").lower():
            return r.id
        if v_lower in (r.area or "").lower():
            return r.id
    raise click.UsageError(f"no region found matching: {v}")


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
