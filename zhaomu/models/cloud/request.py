from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class OrderRequest:
    productId: int
    disk: int = 0
    diskData: int = 0
    bandwidth: int = 0
    imageId: int = 0
    paymentCycle: int = 1

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RenewRequest:
    paymentCycle: int = 1

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UpgradeRequest:
    productId: Optional[int] = None
    disk: Optional[int] = None
    diskData: Optional[int] = None
    bandwidth: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class UpgradePriceRequest:
    productId: Optional[int] = None
    disk: Optional[int] = None
    diskData: Optional[int] = None
    bandwidth: Optional[int] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class RebuildRequest:
    imageId: int = 0

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ResetPasswordRequest:
    password: str = ""

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class AutoRenewRequest:
    enable: int = 1

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class NoteRequest:
    note: str = ""

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}
