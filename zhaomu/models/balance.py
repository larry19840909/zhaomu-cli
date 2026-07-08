from dataclasses import dataclass
from typing import Any, Dict

from zhaomu.models.base import _from_dict


@dataclass
class Balance:
    balance: float = 0.0

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Balance":
        return _from_dict(cls, data)
