from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta

from .. import LABEL, POLICY_VERSION, __version__
from .. import generators
from ..mapping import DatasetContext
from ..models import DatePolicy, Options
from .detection import detect_sensitive
from .detector import detect_document_type
from .models import DocumentType, FinancialSanitizationResult
from .parsers import PARSERS
from .pdf import extract_pdf, render_clean_pdf
from .validation import validate_preservation

DATE = re.compile(r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b")
PDF_LABEL = "DOCUMENTO SANITIZADO PARA DATASET - SIN VALIDEZ DOCUMENTAL / FISCAL"


class FinancialDocumentSanitizer:
    def __init__(self, context: DatasetContext, options: Options | None = None) -> None:
        self.context = context
        self.options = options or Options()

    def inspect(self, pdf: bytes, forced_type: DocumentType | None = None) -> dict[str, object]:
        pages, metadata = extract_pdf(pdf)
        kind = forced_type or detect_document_type("\n".join(pages))
        document = PARSERS[kind].parse(pages, metadata)
        occurrences = detect_sensitive(document)
        counts = Counter(item.kind for item in occurrences)
        return {"documentType": kind.value, "pages": len(pages), "entities": dict(counts),
                "financialValues": len(document.financial_values), "warnings": document.warnings}

    def sanitize(self, pdf: bytes, forced_type: DocumentType | None = None) -> FinancialSanitizationResult:
        pages, metadata = extract_pdf(pdf)
        kind = forced_type or detect_document_type("\n".join(pages))
        original = PARSERS[kind].parse(pages, metadata)
        occurrences = detect_sensitive(original)
        primary_names = [item.value for item in occurrences if item.kind == "name"]
        primary_rfcs = [item.value for item in occurrences if item.kind == "rfc"]
        if primary_names and primary_rfcs:
            self.context.link_entity(primary_names[0], primary_rfcs[0])
        counts: dict[str, int] = {}
        replacements: dict[tuple[str, str], str] = {}
        for occurrence in occurrences:
            key = (occurrence.kind, occurrence.value)
            if key not in replacements: replacements[key] = self._replacement(*key)
            occurrence.replacement = replacements[key]; counts[occurrence.kind] = counts.get(occurrence.kind, 0) + 1
        clean_pages = [self._replace_page(page, page_number, occurrences) for page_number, page in enumerate(pages, 1)]
        clean_pages = [self._dates(page) for page in clean_pages]
        transformed = PARSERS[kind].parse(clean_pages, {})
        validate_preservation(original, transformed)
        output = render_clean_pdf(clean_pages, PDF_LABEL)
        extracted_pages, sanitized_metadata = extract_pdf(output)
        residual_text = "\n".join(extracted_pages) + "\n" + json.dumps(sanitized_metadata)
        residual = [item.value for item in occurrences if len(item.value) >= 3 and item.value in residual_text]
        if residual: raise ValueError("RESIDUAL_PII")
        # Una segunda detección estructural sólo admite identificadores sintéticos ya registrados.
        post = PARSERS[kind].parse(extracted_pages, sanitized_metadata); detect_sensitive(post)
        validate_preservation(original, post)
        sidecar = {"sanitized": True, "purpose": "AI_DATASET", "documentType": kind.value,
            "sanitizerVersion": __version__, "policyVersion": POLICY_VERSION,
            "mode": self.options.mode.value, "originalFinancialSemanticsPreserved": True,
            "residualScan": "PASS", "pages": len(extracted_pages), "transformations": counts,
            "sanitizedSourceHash": hashlib.sha256(output).hexdigest(), "label": LABEL}
        return FinancialSanitizationResult(output, transformed, counts,
            json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True).encode())

    def _replacement(self, kind: str, value: str) -> str:
        if kind == "rfc": return self.context.map(kind, value, generators.rfc)
        if kind == "name": return self.context.map(kind, value, generators.name)
        if kind == "clabe": return self.context.map(kind, value, generators.clabe)
        if kind == "account":
            return self.context.map(kind, value, lambda digest: generators.account(digest, len(value)))
        return self.context.map(kind, value, lambda digest: _shape_identifier(value, digest))

    @staticmethod
    def _replace_page(page: str, page_number: int, occurrences) -> str:
        result = page
        relevant = {(item.value, item.replacement) for item in occurrences if item.page == page_number}
        for value, replacement in sorted(relevant, key=lambda item: len(item[0]), reverse=True):
            result = result.replace(value, replacement)
        return result

    def _dates(self, text: str) -> str:
        if self.options.date_policy == DatePolicy.KEEP: return text
        def replace(match: re.Match[str]) -> str:
            separator = "/" if "/" in match.group() else "-"
            date = datetime.strptime(match.group(), f"%d{separator}%m{separator}%Y")
            if self.options.date_policy == DatePolicy.GENERALIZE: return date.strftime("%m/%Y")
            return (date + timedelta(days=self.options.date_shift_days)).strftime(f"%d{separator}%m{separator}%Y")
        return DATE.sub(replace, text)


def _shape_identifier(original: str, digest: bytes) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    chars = iter(digest * ((len(original) // len(digest)) + 1))
    return "".join((str(next(chars) % 10) if char.isdigit() else alphabet[next(chars) % len(alphabet)])
                   if char.isalnum() else char for char in original)
