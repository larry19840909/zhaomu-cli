from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from zhaomu.models.base import _from_dict


@dataclass
class CloudProduct:
    id: int
    cpu: int = 0
    ram: int = 0
    disk: int = 0
    diskMax: int = 0
    diskData: int = 0
    diskDataMax: int = 0
    diskMedia: str = ""
    bandwidth: Optional[int] = None
    bandwidthMax: Optional[int] = None
    traffic: int = 0
    priceHour: float = 0.0
    price: int = 0
    priceQuarter: int = 0
    priceHalfYear: int = 0
    priceYear: int = 0
    tags: str = ""
    outOfStock: int = 0
    noWindows: Optional[int] = None
    region_id: int = 0
    minPaymentCycle: int = 0

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "CloudProduct":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["CloudProduct"]:
        return [cls._from_dict(item) for item in data]


@dataclass
class Image:
    id: int
    name: str = ""
    type: str = ""

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Image":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["Image"]:
        return [cls._from_dict(item) for item in data]


@dataclass
class CompareItem:
    target_id: int = 0
    name: str = ""
    explain: str = ""

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "CompareItem":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["CompareItem"]:
        return [cls._from_dict(item) for item in data]
