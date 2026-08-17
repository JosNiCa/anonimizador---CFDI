from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DocumentType(str, Enum):
    CFDI = "CFDI"
    BANK_STATEMENT = "BANK_STATEMENT"
    TRIAL_BALANCE = "TRIAL_BALANCE"
    AUXILIARY_LEDGER = "AUXILIARY_LEDGER"


class DataClass(str, Enum):
    IDENTITY = "IDENTITY"
    STRUCTURAL_IDENTIFIER = "STRUCTURAL_IDENTIFIER"
    FINANCIAL_VALUE = "FINANCIAL_VALUE"
    FINANCIAL_SEMANTIC = "FINANCIAL_SEMANTIC"
    DOCUMENT_STRUCTURE = "DOCUMENT_STRUCTURE"


@dataclass(frozen=True)
class TextFragment:
    text: str
    page: int
    bbox: tuple[float, float, float, float] | None = None


@dataclass
class SensitiveOccurrence:
    kind: str
    value: str
    page: int
    bbox: tuple[float, float, float, float] | None
    context: str
    replacement: str = ""


@dataclass
class FinancialDocument:
    document_type: DocumentType
    pages: list[str]
    metadata: dict[str, str] = field(default_factory=dict)
    fragments: list[TextFragment] = field(default_factory=list)
    occurrences: list[SensitiveOccurrence] = field(default_factory=list)
    financial_values: list[str] = field(default_factory=list)
    account_codes: list[str] = field(default_factory=list)
    movement_count: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\f\n".join(self.pages)


@dataclass
class FinancialSanitizationResult:
    content: bytes
    document: FinancialDocument
    transformations: dict[str, int]
    sidecar: bytes
    financial_preservation: str = "PASS"

