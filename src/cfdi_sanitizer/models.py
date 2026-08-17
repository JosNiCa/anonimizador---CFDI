from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Mode(str, Enum):
    IDENTITY_ONLY = "IDENTITY_ONLY"
    SYNTHETIC_REINFORCED = "SYNTHETIC_REINFORCED"


class DatePolicy(str, Enum):
    KEEP = "KEEP"
    SHIFT = "SHIFT"
    GENERALIZE = "GENERALIZE"


class SanitizationError(Exception):
    code = "SANITIZATION_ERROR"


class MalformedDocument(SanitizationError):
    code = "MALFORMED_DOCUMENT"


class UnsupportedDocument(SanitizationError):
    code = "UNSUPPORTED_DOCUMENT"


class ResidualPII(SanitizationError):
    code = "RESIDUAL_PII"


@dataclass
class Options:
    mode: Mode = Mode.IDENTITY_ONLY
    date_policy: DatePolicy = DatePolicy.KEEP
    date_shift_days: int = 47


@dataclass
class Result:
    content: bytes
    json_content: bytes | None
    document_id: str
    transformations: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    financial_status: str = "PRESERVED"

