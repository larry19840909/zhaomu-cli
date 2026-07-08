from typing import TYPE_CHECKING, List, Optional

from zhaomu.models.base import OperationResult
from zhaomu.models.product import Image
from zhaomu.models.cloud.server import CloudServer, CloudServerDetail
from zhaomu.models.cloud.request import (
    OrderRequest, RenewRequest, UpgradeRequest, UpgradePriceRequest,
    RebuildRequest, ResetPasswordRequest, AutoRenewRequest, NoteRequest,
)

if TYPE_CHECKING:
    from zhaomu.client import ZhaomuClient


class CloudAPI:
    def __init__(self, client: "ZhaomuClient"):
        self._client = client

    def list(self) -> List[CloudServer]:
        data = self._client.get("/cloud")
        return CloudServer._from_list(data)

    def info(self, instance_id: int) -> CloudServerDetail:
        data = self._client.get(f"/cloud/{instance_id}")
        return CloudServerDetail._from_dict(data)

    def order(self, req: OrderRequest) -> OperationResult:
        data = self._client.post("/cloud/order", data=req.to_dict())
        return OperationResult._from_dict(data)

    def images(self, product_id: int) -> List[Image]:
        data = self._client.get(f"/image/product/{product_id}")
        return Image._from_list(data)

    def renew(self, instance_id: int, req: RenewRequest) -> OperationResult:
        data = self._client.post(f"/cloud/renew/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def upgrade(self, instance_id: int, req: UpgradeRequest) -> OperationResult:
        data = self._client.post(f"/cloud/upgrade/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def upgrade_price(self, instance_id: int, req: UpgradePriceRequest) -> OperationResult:
        data = self._client.post(f"/cloud/upgrade-price/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def destroy(self, instance_id: int) -> OperationResult:
        data = self._client.delete(f"/cloud/destroy/{instance_id}")
        return OperationResult._from_dict(data)

    def reboot(self, instance_id: int) -> OperationResult:
        data = self._client.post(f"/cloud/reboot/{instance_id}")
        return OperationResult._from_dict(data)

    def shutdown(self, instance_id: int) -> OperationResult:
        data = self._client.post(f"/cloud/shutdown/{instance_id}")
        return OperationResult._from_dict(data)

    def rebuild(self, instance_id: int, req: RebuildRequest) -> OperationResult:
        data = self._client.post(f"/cloud/rebuild/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def rebuild_images(self, instance_id: int) -> List[Image]:
        data = self._client.get(f"/image/cloud/{instance_id}")
        return Image._from_list(data)

    def reset_password(self, instance_id: int, req: ResetPasswordRequest) -> OperationResult:
        data = self._client.post(f"/cloud/password/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def console(self, instance_id: int) -> OperationResult:
        data = self._client.get(f"/cloud/novnc/{instance_id}")
        return OperationResult._from_dict(data)

    def auto_renew(self, instance_id: int, req: AutoRenewRequest) -> OperationResult:
        data = self._client.post(f"/cloud/auto-renew/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def note(self, instance_id: int, req: NoteRequest) -> OperationResult:
        data = self._client.post(f"/cloud/note/{instance_id}", data=req.to_dict())
        return OperationResult._from_dict(data)

    def refresh_traffic(self, instance_id: int) -> OperationResult:
        data = self._client.post(f"/cloud/traffic/{instance_id}")
        return OperationResult._from_dict(data)
