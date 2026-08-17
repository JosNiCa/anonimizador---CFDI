from __future__ import annotations

import unicodedata

from .models import DocumentType

SIGNALS = {
    DocumentType.BANK_STATEMENT: ("ESTADO DE CUENTA", "SALDO INICIAL", "SALDO FINAL", "RETIROS", "CLABE"),
    DocumentType.TRIAL_BALANCE: ("BALANZA DE COMPROBACION", "SALDO INICIAL", "DEBE", "HABER", "EJERCICIO"),
    DocumentType.AUXILIARY_LEDGER: ("REPORTE DE AUXILIARES", "TIPO", "NUMERO", "CONCEPTO", "DEBE", "HABER", "SALDO"),
}


def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.upper()) if not unicodedata.combining(c))


def detect_document_type(text: str) -> DocumentType:
    clean = normalized(text)
    scores = {kind: sum(signal in clean for signal in signals) for kind, signals in SIGNALS.items()}
    kind, score = max(scores.items(), key=lambda item: item[1])
    if score < 3:
        raise ValueError("DOCUMENT_REQUIRES_MANUAL_REVIEW")
    return kind

