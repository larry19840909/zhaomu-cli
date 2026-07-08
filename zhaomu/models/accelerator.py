from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from zhaomu.models.base import _from_dict, OperationResult


@dataclass
class Accelerator:
    id: int
    type: str = ""
    domain: str = ""
    region: str = ""
    ip: str = ""
    port: int = 0
    area: str = ""
    startTime: str = ""
    endTime: str = ""
    renewPrice: float = 0.0
    paymentCycle: int = 0

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Accelerator":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["Accelerator"]:
        return [cls._from_dict(item) for item in data]


@dataclass
class AcceleratorOrderRequest:
    productId: int = 0
    region: str = ""
    ip: str = ""
    port: int = 0
    area: str = ""
    paymentCycle: int = 1

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AcceleratorModifyRequest:
    ip: str = ""
    area: str = ""

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AcceleratorPortRequest:
    port: int = 0

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TrafficUsage:
    """加速器每日流量用量记录。"""
    Date: int = 0        # Unix 时间戳
    Traffic: float = 0.0  # 流量用量（GB）
    BillingState: str = ""  # 计费状态 "Yes" / "No"

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "TrafficUsage":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["TrafficUsage"]:
        return [cls._from_dict(item) for item in data]
