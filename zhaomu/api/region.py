from typing import TYPE_CHECKING, List

from zhaomu.models.region import Region

if TYPE_CHECKING:
    from zhaomu.client import ZhaomuClient


class RegionAPI:
    def __init__(self, client: "ZhaomuClient"):
        self._client = client

    def list(self) -> List[Region]:
        data = self._client.get("/region")
        return Region._from_list(data)

    def info(self, region_id: int) -> Region:
        data = self._client.get(f"/region/{region_id}")
        return Region._from_dict(data)
