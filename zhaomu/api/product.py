from typing import TYPE_CHECKING, Any, Dict, List

from zhaomu.models.product import CloudProduct, Image, CompareItem

if TYPE_CHECKING:
    from zhaomu.client import ZhaomuClient


class ProductAPI:
    def __init__(self, client: "ZhaomuClient"):
        self._client = client

    def list(self, region_id: int) -> List[CloudProduct]:
        data = self._client.get(f"/product/region/{region_id}")
        return CloudProduct._from_list(data)

    def info(self, product_id: int) -> CloudProduct:
        data = self._client.get(f"/product/{product_id}")
        return CloudProduct._from_dict(data)

    def price(self, product_id: int, disk: int = None, disk_data: int = None,
              bandwidth: int = None) -> Dict[str, float]:
        params = {}
        if disk is not None:
            params["disk"] = disk
        if disk_data is not None:
            params["diskData"] = disk_data
        if bandwidth is not None:
            params["bandwidth"] = bandwidth
        return self._client.get(f"/product/price/{product_id}", params=params)

    def compare(self, region_id: int) -> List[CompareItem]:
        data = self._client.get(f"/compare/region/{region_id}")
        return CompareItem._from_list(data)
