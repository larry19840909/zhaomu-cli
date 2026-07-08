from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from zhaomu.models.base import _from_dict


@dataclass
class CloudServer:
    id: int
    ip: str = ""
    root: str = ""
    cpu: int = 0
    ram: int = 0
    disk: int = 0
    diskData: int = 0
    diskMedia: str = ""
    bandwidth: Optional[int] = None
    traffic: int = 0
    image: str = ""
    renewPrice: float = 0.0
    paymentCycle: int = 0
    priceHour: Optional[float] = None
    price: int = 0
    priceQuarter: int = 0
    priceHalfYear: int = 0
    priceYear: int = 0
    startTime: str = ""
    endTime: str = ""
    status: int = 0
    note: Optional[str] = None
    noteUser: Optional[str] = None
    isAutoRenew: int = 0
    region_id: int = 0

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "CloudServer":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["CloudServer"]:
        return [cls._from_dict(item) for item in data]


@dataclass
class CloudServerDetail:
    id: int
    ip: str = ""
    root: str = ""
    password: str = ""
    cpu: int = 0
    ram: int = 0
    disk: int = 0
    diskData: int = 0
    diskMedia: str = ""
    bandwidth: Optional[int] = None
    traffic: int = 0
    image: str = ""
    renewPrice: float = 0.0
    paymentCycle: int = 0
    priceHour: Optional[float] = None
    price: int = 0
    priceQuarter: int = 0
    priceHalfYear: int = 0
    priceYear: int = 0
    startTime: str = ""
    endTime: str = ""
    status: int = 0
    note: Optional[str] = None
    noteUser: Optional[str] = None
    isAutoRenew: int = 0
    region_id: int = 0

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "CloudServerDetail":
        return _from_dict(cls, data)
