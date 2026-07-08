from typing import TYPE_CHECKING, List

from zhaomu.models.base import OperationResult
from zhaomu.models.accelerator import (
    Accelerator, AcceleratorOrderRequest, AcceleratorModifyRequest,
    AcceleratorPortRequest,
)

if TYPE_CHECKING:
    from zhaomu.client import ZhaomuClient


class AcceleratorAPI:
    def __init__(self, client: "ZhaomuClient"):
        self._client = client

    def list(self) -> List[Accelerator]:
        data = self._client.get("/accelerator")
        return Accelerator._from_list(data)

    def info(self, accelerator_id: int) -> Accelerator:
        data = self._client.get(f"/accelerator/{accelerator_id}")
        return Accelerator._from_dict(data)

    def order(self, req: AcceleratorOrderRequest) -> OperationResult:
        data = self._client.post("/accelerator/order", data=req.to_dict())
        return OperationResult._from_dict(data)

    def renew(self, accelerator_id: int, payment_cycle: int) -> OperationResult:
        data = self._client.post(f"/accelerator/renew/{accelerator_id}", data={"paymentCycle": payment_cycle})
        return OperationResult._from_dict(data)

    def upgrade(self, accelerator_id: int, payment_cycle: int) -> OperationResult:
        data = self._client.post(f"/accelerator/upgrade/{accelerator_id}", data={"paymentCycle": payment_cycle})
        return OperationResult._from_dict(data)

    def modify_ip(self, accelerator_id: int, req: AcceleratorModifyRequest) -> OperationResult:
        data = self._client.post(f"/accelerator/modify/{accelerator_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def modify_port(self, accelerator_id: int, req: AcceleratorPortRequest) -> OperationResult:
        data = self._client.post(f"/accelerator/port/{accelerator_id}", data=req.to_dict())
        return OperationResult._from_dict(data)
