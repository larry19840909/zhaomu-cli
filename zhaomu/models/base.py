from dataclasses import dataclass, fields
from typing import Any, Dict, Optional, Type, TypeVar, get_origin, get_args, Union

T = TypeVar("T")


def _resolve_bare_types(tp: type) -> set[type]:
    """Extract bare types from an annotation, handling Optional/Union."""
    origin = get_origin(tp)
    if origin is Union:
        return {a for a in get_args(tp) if a is not type(None)}
    return {tp}


def _from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
    field_names = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    for f in fields(cls):
        if f.name in filtered and isinstance(filtered[f.name], str):
            bare_types = _resolve_bare_types(f.type)
            if float in bare_types:
                try:
                    filtered[f.name] = float(filtered[f.name])
                except (ValueError, TypeError):
                    pass
            elif int in bare_types:
                try:
                    filtered[f.name] = int(float(filtered[f.name]))
                except (ValueError, TypeError):
                    pass
    return cls(**filtered)


@dataclass
class OperationResult:
    success: bool
    message: str
    info: Optional[Dict[str, Any]] = None

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "OperationResult":
        return cls(
            success=data.get("success", False),
            message=data.get("message") or "",
            info=data.get("info"),
        )
