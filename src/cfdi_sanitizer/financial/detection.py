from __future__ import annotations

import re

from .models import FinancialDocument, SensitiveOccurrence

RFC = re.compile(r"(?i)\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b")
CLABE = re.compile(r"(?<!\d)\d{18}(?!\d)")
LABELED_NUMBER = re.compile(r"(?i)\b(CLIENTE|CUENTA|CTA|REFERENCIA|REF|NUMERO|NÚMERO|OPERACION|OPERACIÓN|RASTREO)\s*[:#-]?\s*([A-Z0-9-]{4,40})")
INVOICE = re.compile(r"(?i)\b(FACTURA|TICKET|POLIZA|PÓLIZA)\s*[:#-]?\s*([A-Z0-9-]{2,30})")
LABELED_ORG = re.compile(r"(?im)\b(?:RAZON SOCIAL|RAZÓN SOCIAL|TITULAR|BENEF|BENEFICIARIO|ORDENANTE|CLIENTE|PROVEEDOR)\s*:\s*([^\n]{4,100})")
INLINE_ORG = re.compile(r"(?i)\b((?:[A-ZÁÉÍÓÚÑ&]+\s+){1,8}(?:SA DE CV|S DE RL DE CV|SAPI DE CV))\b")
GENERIC_ACCOUNTS = {"BANCOS", "BANCOS NACIONALES", "PROVEEDORES", "IVA A FAVOR", "CAJA", "SUELDOS Y SALARIOS", "VENTAS GRAVADAS TASA 16%"}


def detect_sensitive(document: FinancialDocument) -> list[SensitiveOccurrence]:
    found: dict[tuple[str, str, int], SensitiveOccurrence] = {}
    for page_number, page in enumerate(document.pages, 1):
        for kind, pattern in (("rfc", RFC), ("clabe", CLABE)):
            for match in pattern.finditer(page):
                found[(kind, match.group(), page_number)] = _occ(kind, match.group(), page_number, page, match.start())
        for match in LABELED_NUMBER.finditer(page):
            label, value = match.groups(); kind = "account" if label.upper() in {"CUENTA", "CTA"} else "identifier"
            found[(kind, value, page_number)] = _occ(kind, value, page_number, page, match.start(2))
        for match in INVOICE.finditer(page):
            value = match.group(2); found[("identifier", value, page_number)] = _occ("identifier", value, page_number, page, match.start(2))
        for pattern in (LABELED_ORG, INLINE_ORG):
            for match in pattern.finditer(page):
                value = match.group(1).strip(" :-")
                value = re.sub(r"(?i)^(?:COBRO CLIENTE|PAGO PROVEEDOR|CLIENTE|PROVEEDOR)\s+", "", value)
                if value.upper() not in GENERIC_ACCOUNTS:
                    found[("name", value, page_number)] = _occ("name", value, page_number, page, match.start(1))
    document.occurrences = sorted(found.values(), key=lambda item: (item.page, -len(item.value)))
    return document.occurrences


def _occ(kind: str, value: str, page: int, text: str, position: int) -> SensitiveOccurrence:
    context = text[max(0, position - 24):position] + "[…]" + text[position + len(value):position + len(value) + 24]
    return SensitiveOccurrence(kind, value, page, None, context)
