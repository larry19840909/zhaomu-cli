from dataclasses import dataclass
from typing import Dict, Any, List

from zhaomu.models.base import _from_dict


@dataclass
class Region:
    id: int
    continent: str = ""
    continentEn: str = ""
    country: str = ""
    countryEn: str = ""
    area: str = ""
    areaEn: str = ""
    province: str = ""
    provinceEn: str = ""
    city: str = ""
    cityEn: str = ""
    zone: str = ""

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Region":
        return _from_dict(cls, data)

    @classmethod
    def _from_list(cls, data: List[Dict[str, Any]]) -> List["Region"]:
        return [cls._from_dict(item) for item in data]
