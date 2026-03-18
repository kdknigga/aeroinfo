"""Helper functions for snapshot-based parser regression tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Date, Enum, Float, Integer, String, inspect

from aeroinfo.database.enums import NASREnum

if TYPE_CHECKING:
    from aeroinfo.database.base import Base


def extract_record(instance: Base) -> dict[str, Any]:
    """
    Serialize all mapped ORM columns of *instance* to a plain dict.

    Serialization rules:
    - None/null values pass through as None.
    - NASREnum values serialize to {"code": ..., "description": ...}.
    - datetime.date values serialize to ISO 8601 strings (e.g. "2024-01-15").
    - Scalar types (String, Integer, Float, Boolean) pass through as-is.
    - Unknown column types raise TypeError — update this function when new
      SQLAlchemy column types are added to the models.
    """
    mapper = inspect(type(instance))
    result: dict[str, Any] = {}
    for col in mapper.columns:
        val = getattr(instance, col.key)
        if val is None:
            result[col.key] = None
        elif isinstance(col.type, Enum) and issubclass(col.type.enum_class, NASREnum):
            result[col.key] = {"code": val.value, "description": val.description}
        elif isinstance(col.type, Date):
            result[col.key] = val.isoformat()
        elif isinstance(col.type, (String, Integer, Float, Boolean)):
            result[col.key] = val
        else:
            msg = (
                f"Column {col.key!r} has unsupported type "
                f"{type(col.type).__name__!r}. "
                "Update extract_record() in tests/snapshot_helpers.py "
                "to handle this type."
            )
            raise TypeError(msg)
    return result
