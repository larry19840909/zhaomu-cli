from typing import TYPE_CHECKING

from zhaomu.models.balance import Balance

if TYPE_CHECKING:
    from zhaomu.client import ZhaomuClient


class OtherAPI:
    def __init__(self, client: "ZhaomuClient"):
        self._client = client

    def balance(self) -> Balance:
        data = self._client.get("/other/balance")
        return Balance._from_dict(data)
