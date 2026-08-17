from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import POLICY_VERSION, __version__
from .core import Sanitizer
from .mapping import DatasetContext
from .models import Options


def inputs(path: Path) -> list[Path]:
    return sorted((p for p in (path.rglob("*") if path.is_dir() else [path])
                   if p.is_file() and p.suffix.lower() in {".xml", ".json"}))


def inspect(path: Path) -> dict[str, int]:
    sanitizer = Sanitizer(DatasetContext("inspection-only"))
    sanitizer.sanitize_file(path)
    return sanitizer.counts


def run(source: Path, output: Path, seed: str, options: Options, dry_run: bool = False) -> dict:
    files = inputs(source)
    if output.resolve() == source.resolve() or (source.is_file() and output.resolve() == source.parent.resolve()):
        raise ValueError("La salida debe ser distinta de la ubicación original")
    context = DatasetContext(seed)
    totals: dict[str, int] = {}; exported = blocked = 0; errors: list[str] = []
    if not dry_run: output.mkdir(parents=True, exist_ok=True)
    for index, path in enumerate(files, 1):
        sanitizer = Sanitizer(context, options)
        try:
            result = sanitizer.sanitize_file(path)
            for key, count in result.transformations.items(): totals[key] = totals.get(key, 0) + count
            if not dry_run:
                basename = f"DOC-{index:06d}"
                suffix = path.suffix.lower()
                _atomic(output / f"{basename}.sanitized{suffix}", result.content)
                if result.json_content:
                    _atomic(output / f"{basename}.sanitized.json", result.json_content)
            exported += 1
        except Exception as exc:
            blocked += 1; errors.append(getattr(exc, "code", type(exc).__name__))
    manifest = {"sanitizerVersion": __version__, "policyVersion": POLICY_VERSION,
        "createdAt": datetime.now(timezone.utc).isoformat(), "mode": options.mode.value,
        "documentsProcessed": len(files), "documentsExported": exported,
        "documentsBlocked": blocked, "transformations": totals,
        "validation": {"structural": "PASS" if not blocked else "PARTIAL",
                       "residualSensitiveData": "PASS" if not blocked else "BLOCKED"},
        "errors": errors, "riskNotice": "Puede persistir riesgo de reidentificación indirecta."}
    if not dry_run: _atomic(output / "sanitization_manifest.json", json.dumps(manifest, indent=2).encode())
    return manifest


def verify(path: Path) -> dict:
    manifest_path = path / "sanitization_manifest.json"
    files = list(path.glob("*.sanitized.*"))
    labeled = sum(b"SIN VALIDEZ FISCAL" in p.read_bytes() for p in files)
    return {"files": len(files), "labeled": labeled, "manifest": manifest_path.exists(),
            "status": "PASS" if files and labeled == len(files) and manifest_path.exists() else "FAIL"}


def _atomic(path: Path, content: bytes) -> None:
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as stream: stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temp, path)
    except Exception:
        try: os.unlink(temp)
        except FileNotFoundError: pass
        raise

