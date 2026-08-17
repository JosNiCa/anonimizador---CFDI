from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from xml.etree import ElementTree as SafeET

from . import LABEL, POLICY_VERSION, __version__
from . import generators
from .mapping import DatasetContext
from .models import DatePolicy, MalformedDocument, Options, Result, UnsupportedDocument
from .policy import POLICY, SENSITIVE_HINTS

CFDI_NS = "http://www.sat.gob.mx/cfd/4"
SENSITIVE_PATTERNS = {
    "email": re.compile(r"(?i)\b[\w.+-]+@[\w.-]+\.[A-Z]{2,}\b"),
    "uuid": re.compile(r"(?i)\b[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\b"),
    "rfc": re.compile(r"(?i)\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b"),
    "clabe": re.compile(r"(?<!\d)\d{18}(?!\d)"),
}


class Sanitizer:
    def __init__(self, context: DatasetContext, options: Options | None = None) -> None:
        self.context = context
        self.options = options or Options()
        self.counts: dict[str, int] = {}
        self.warnings: list[str] = []

    def sanitize_file(self, path: Path) -> Result:
        data = path.read_bytes()
        if path.suffix.lower() == ".xml": return self.sanitize_xml(data)
        if path.suffix.lower() == ".json": return self.sanitize_json(data)
        raise UnsupportedDocument("Sólo se admiten XML y JSON")

    def sanitize_xml(self, data: bytes) -> Result:
        if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
            raise MalformedDocument("DTD y entidades están prohibidos")
        try: root = SafeET.fromstring(data)
        except Exception as exc: raise MalformedDocument("XML mal formado") from exc
        if root.tag != f"{{{CFDI_NS}}}Comprobante" or root.attrib.get("Version") != "4.0":
            raise UnsupportedDocument("Se requiere CFDI 4.0")
        for element in root.iter():
            if "Rfc" in element.attrib and "Nombre" in element.attrib:
                self.context.link_entity(element.attrib["Nombre"], element.attrib["Rfc"])
            for key, value in list(element.attrib.items()):
                element.attrib[key] = self._transform(key, value)
            if element.text and element.text.strip():
                element.text = self._free_text(element.text)
        xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        marker = ("\n<!-- DOCUMENTO SANITIZADO PARA DATASET — SIN VALIDEZ FISCAL; "
                  "NO UTILIZAR COMO COMPROBANTE FISCAL -->\n").encode()
        xml = xml.replace(b"?>", b"?>" + marker, 1)
        self._assert_no_originals(xml.decode("utf-8"))
        canonical = self._xml_to_json(root)
        json_bytes = self._finish_json(canonical)
        doc_id = self._map("identifier", hashlib.sha256(data).hexdigest())
        return Result(xml, json_bytes, doc_id, dict(self.counts), list(self.warnings),
                      "PRESERVED" if self.options.mode.value == "IDENTITY_ONLY" else "SKIPPED_UNSAFE_TRANSFORMATION")

    def sanitize_json(self, data: bytes) -> Result:
        try: obj = json.loads(data)
        except (ValueError, UnicodeDecodeError) as exc: raise MalformedDocument("JSON mal formado") from exc
        if not isinstance(obj, dict): raise UnsupportedDocument("El contrato JSON debe ser un objeto")
        clean = self._walk_json(obj)
        output = self._finish_json(clean)
        self._assert_no_originals(output.decode())
        doc_id = self._map("identifier", hashlib.sha256(data).hexdigest())
        return Result(output, None, doc_id, dict(self.counts), list(self.warnings))

    def _walk_json(self, value: Any, key: str = "") -> Any:
        if isinstance(value, dict): return {k: self._walk_json(v, k) for k, v in value.items() if self._action(k) != "remove"}
        if isinstance(value, list): return [self._walk_json(v, key) for v in value]
        if isinstance(value, str): return self._transform(key, value)
        return value

    def _action(self, key: str) -> str | None:
        normalized = re.sub(r"[^a-z0-9]", "", key.lower())
        return POLICY.get(normalized)

    def _transform(self, key: str, value: str) -> str:
        action = self._action(key)
        if action == "remove": return ""
        if action == "neutralize": self._inc(action); return "SANITIZED-NO-FISCAL-VALIDITY"
        if action == "postal": self._inc(action); return "00000"
        if action == "address": self._inc(action); return "DOMICILIO SINTETICO NO REAL"
        if action: return self._map(action, value)
        if self._is_date(key, value): return self._date(value)
        normalized = re.sub(r"[^a-z0-9]", "", key.lower())
        if any(hint in normalized for hint in SENSITIVE_HINTS):
            self.warnings.append(f"UNKNOWN_SENSITIVE_FIELD:{key}")
        return self._free_text(value)

    def _map(self, category: str, value: str) -> str:
        factories = {"rfc": generators.rfc, "name": generators.name, "email": generators.email,
                     "phone": generators.phone, "account": generators.account,
                     "uuid": generators.synthetic_uuid, "identifier": generators.identifier}
        self._inc(category)
        return self.context.map(category, value, factories[category])

    def _free_text(self, value: str) -> str:
        result = value
        for category, pattern in SENSITIVE_PATTERNS.items():
            result = pattern.sub(lambda m: self._map(category, m.group()), result)
        return result

    def _date(self, value: str) -> str:
        if self.options.date_policy == DatePolicy.KEEP: return value
        try: dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError: return value
        if self.options.date_policy == DatePolicy.GENERALIZE: return dt.strftime("%Y-%m")
        return (dt + timedelta(days=self.options.date_shift_days)).isoformat(timespec="seconds")

    @staticmethod
    def _is_date(key: str, value: str) -> bool:
        return "fecha" in key.lower() and len(value) >= 7

    def _finish_json(self, obj: dict[str, Any]) -> bytes:
        obj["datasetSanitization"] = {"sanitized": True, "purpose": "AI_DATASET",
            "fiscalValidity": False, "label": LABEL, "sanitizerVersion": __version__,
            "policyVersion": POLICY_VERSION, "sanitizationMode": self.options.mode.value}
        raw = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode()
        obj["datasetSanitization"]["sanitizedSourceHash"] = hashlib.sha256(raw).hexdigest()
        return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode()

    @staticmethod
    def _xml_to_json(root: ET.Element) -> dict[str, Any]:
        def node(e: ET.Element) -> dict[str, Any]:
            result: dict[str, Any] = {k[:1].lower() + k[1:]: v for k, v in e.attrib.items()}
            for child in e:
                name = child.tag.split("}")[-1]; key = name[:1].lower() + name[1:]
                child_value = node(child)
                if key in result: result[key] = result[key] if isinstance(result[key], list) else [result[key]]; result[key].append(child_value)
                else: result[key] = child_value
            return result
        return {"metadata": {"sourceType": "xml", "rawXmlAvailable": False}, "cfdi": node(root)}

    def _assert_no_originals(self, text: str) -> None:
        leftovers = [v for v in self.context.originals if len(v) >= 4 and v in text]
        if leftovers: raise RuntimeError("RESIDUAL_PII")

    def _inc(self, category: str) -> None: self.counts[category] = self.counts.get(category, 0) + 1
