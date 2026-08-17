from __future__ import annotations

from collections import Counter

from .models import FinancialDocument


def validate_preservation(original: FinancialDocument, sanitized: FinancialDocument) -> None:
    """Compara invariantes; no juzga ni corrige la contabilidad original."""
    if Counter(original.financial_values) != Counter(sanitized.financial_values):
        raise ValueError("FINANCIAL_COHERENCE_ERROR")
    if original.account_codes != sanitized.account_codes:
        raise ValueError("DOCUMENT_STRUCTURE_CHANGED")
    if original.movement_count != sanitized.movement_count:
        raise ValueError("MOVEMENT_COUNT_CHANGED")

