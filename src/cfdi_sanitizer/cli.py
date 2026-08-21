from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

from .batch import inspect, run_batch, verify
from .models import DatePolicy, Mode, Options
from .financial.models import DocumentType


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="cfdi-sanitizer", description="Sanitización local de CFDI y documentos financieros")
    sub = root.add_subparsers(dest="command", required=True)
    sanitize = sub.add_parser("sanitize"); sanitize.add_argument("source", type=Path, nargs="+")
    sanitize.add_argument("--output", type=Path, required=True)
    sanitize.add_argument("--mode", choices=("identity", "synthetic"), default="identity")
    sanitize.add_argument("--seed", help="Secreto del dataset; no se registra")
    sanitize.add_argument("--project", help="Alias compatible; no se exporta")
    sanitize.add_argument("--dates", choices=("keep", "shift", "generalize"), default="keep")
    sanitize.add_argument("--dry-run", action="store_true")
    sanitize.add_argument("--document-type", choices=("bank-statement", "trial-balance", "auxiliary-ledger"))
    check = sub.add_parser("verify"); check.add_argument("dataset", type=Path)
    scan = sub.add_parser("inspect"); scan.add_argument("document", type=Path)
    sub.add_parser("gui")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "gui":
        from .ui import main as gui_main
        gui_main(); return 0
    if args.command == "verify": result = verify(args.dataset)
    elif args.command == "inspect": result = {"categories": inspect(args.document)}
    else:
        mode = Mode.IDENTITY_ONLY if args.mode == "identity" else Mode.SYNTHETIC_REINFORCED
        dates = DatePolicy(args.dates.upper())
        seed = args.seed or secrets.token_urlsafe(32)
        forced = _document_type(args.document_type)
        result = run_batch(args.source, args.output, seed, Options(mode, dates), args.dry_run, forced)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("status", "PASS") != "FAIL" else 1


def _document_type(value: str | None) -> DocumentType | None:
    if value is None: return None
    return {"bank-statement": DocumentType.BANK_STATEMENT,
            "trial-balance": DocumentType.TRIAL_BALANCE,
            "auxiliary-ledger": DocumentType.AUXILIARY_LEDGER}[value]


if __name__ == "__main__": raise SystemExit(main())
