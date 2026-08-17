from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import POLICY_VERSION, __version__
from .core import Sanitizer
from .financial.models import DocumentType
from .financial.service import FinancialDocumentSanitizer
from .mapping import DatasetContext
from .models import Options


def inputs(path: Path) -> list[Path]:
    return sorted((p for p in (path.rglob("*") if path.is_dir() else [path])
                   if p.is_file() and p.suffix.lower() in {".xml", ".json", ".pdf"}))


def inspect(path: Path, forced_type: DocumentType | None = None) -> dict[str, object]:
    if path.suffix.lower() == ".pdf":
        return FinancialDocumentSanitizer(DatasetContext("inspection-only")).inspect(path.read_bytes(), forced_type)
    sanitizer = Sanitizer(DatasetContext("inspection-only"))
    sanitizer.sanitize_file(path)
    result: dict[str, object] = {key: value for key, value in sanitizer.counts.items()}
    return result


def run(source: Path, output: Path, seed: str, options: Options, dry_run: bool = False,
        forced_type: DocumentType | None = None) -> dict:
    files = inputs(source)
    if output.resolve() == source.resolve() or (source.is_file() and output.resolve() == source.parent.resolve()):
        raise ValueError("La salida debe ser distinta de la ubicación original")
    context = DatasetContext(seed)
    totals: dict[str, int] = {}; exported = blocked = 0; errors: list[str] = []
    document_types = {kind.value: 0 for kind in DocumentType}
    if not dry_run: output.mkdir(parents=True, exist_ok=True)
    for index, path in enumerate(files, 1):
        sanitizer = Sanitizer(context, options)
        try:
            if path.suffix.lower() == ".pdf":
                financial_result = FinancialDocumentSanitizer(context, options).sanitize(path.read_bytes(), forced_type)
                result_content = financial_result.content; result_json = None
                result_transformations = financial_result.transformations
                detected_type = financial_result.document.document_type
            else:
                result = sanitizer.sanitize_file(path)
                result_content = result.content; result_json = result.json_content
                result_transformations = result.transformations; detected_type = DocumentType.CFDI
            document_types[detected_type.value] += 1
            for key, count in result_transformations.items(): totals[key] = totals.get(key, 0) + count
            if not dry_run:
                basename = f"DOC-{index:06d}"
                suffix = path.suffix.lower()
                _atomic(output / f"{basename}.sanitized{suffix}", result_content)
                if result_json:
                    _atomic(output / f"{basename}.sanitized.json", result_json)
                if path.suffix.lower() == ".pdf":
                    _atomic(output / f"{basename}.sanitization.json", financial_result.sidecar)
            exported += 1
        except Exception as exc:
            blocked += 1; errors.append(getattr(exc, "code", type(exc).__name__))
    manifest = {"sanitizerVersion": __version__, "policyVersion": POLICY_VERSION,
        "createdAt": datetime.now(timezone.utc).isoformat(), "mode": options.mode.value,
        "documentsProcessed": len(files), "documentsExported": exported,
        "documentsBlocked": blocked, "transformations": totals,
        "documents": document_types,
        "validation": {"structural": "PASS" if not blocked else "PARTIAL",
                       "residualSensitiveData": "PASS" if not blocked else "BLOCKED"},
        "errors": errors, "riskNotice": "Puede persistir riesgo de reidentificación indirecta."}
    if not dry_run: _atomic(output / "sanitization_manifest.json", json.dumps(manifest, indent=2).encode())
    return manifest


def verify(path: Path) -> dict:
    manifest_path = path / "sanitization_manifest.json"
    files = list(path.glob("*.sanitized.*"))
    labels = (b"SIN VALIDEZ FISCAL", b"SIN VALIDEZ DOCUMENTAL / FISCAL")
    labeled = sum(_has_label(p, labels) for p in files)
    return {"files": len(files), "labeled": labeled, "manifest": manifest_path.exists(),
            "status": "PASS" if files and labeled == len(files) and manifest_path.exists() else "FAIL"}


def _has_label(path: Path, labels: tuple[bytes, ...]) -> bool:
    if path.suffix.lower() == ".pdf":
        from .financial.pdf import extract_pdf
        text = "\n".join(extract_pdf(path.read_bytes())[0]).encode()
        return any(label in text for label in labels)
    content = path.read_bytes()
    return any(label in content for label in labels)


def _atomic(path: Path, content: bytes) -> None:
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as stream: stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise
