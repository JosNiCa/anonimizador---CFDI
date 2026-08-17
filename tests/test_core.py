import json
from pathlib import Path

import pytest

from cfdi_sanitizer.batch import run, verify
from cfdi_sanitizer.core import Sanitizer
from cfdi_sanitizer.mapping import DatasetContext
from cfdi_sanitizer.models import DatePolicy, MalformedDocument, Options

FIXTURE = Path(__file__).parent / "fixtures/cfdi.xml"


def test_deterministic_and_preserves_financial_structure():
    raw = FIXTURE.read_bytes()
    one = Sanitizer(DatasetContext("seed")).sanitize_xml(raw)
    two = Sanitizer(DatasetContext("seed")).sanitize_xml(raw)
    assert one.content == two.content
    assert b"AAA010101AAA" not in one.content
    assert b'Total="116.00"' in one.content
    assert b"SIN VALIDEZ FISCAL" in one.content
    canonical = json.loads(one.json_content)
    assert canonical["cfdi"]["emisor"]["rfc"] in one.content.decode()
    assert canonical["datasetSanitization"]["fiscalValidity"] is False


def test_cross_document_relationship_mapping():
    context = DatasetContext("same-dataset")
    sanitizer = Sanitizer(context)
    first = sanitizer.sanitize_xml(FIXTURE.read_bytes()).content
    related = FIXTURE.read_bytes().replace(
        b"<x:Conceptos>", b'<x:CfdiRelacionados TipoRelacion="04"><x:CfdiRelacionado UUID="123E4567-E89B-12D3-A456-426614174000"/></x:CfdiRelacionados><x:Conceptos>')
    second = Sanitizer(context).sanitize_xml(related).content
    synthetic = json.loads(Sanitizer(DatasetContext("same-dataset")).sanitize_xml(FIXTURE.read_bytes()).json_content)["cfdi"]["complemento"]["timbreFiscalDigital"]["uUID"]
    assert synthetic.encode() in first and synthetic.encode() in second


def test_rejects_xxe():
    with pytest.raises(MalformedDocument):
        Sanitizer(DatasetContext("s")).sanitize_xml(b'<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><x/>')


def test_dates_shift_together():
    result = Sanitizer(DatasetContext("s"), Options(date_policy=DatePolicy.SHIFT)).sanitize_xml(FIXTURE.read_bytes())
    assert b"2024-03-02T10:30:00" in result.content


def test_json_preserves_null_empty_and_numbers():
    raw = b'{"metadata":{"documentId":"internal-1","sourceHash":"secret"},"cfdi":{"version":"4.0","folio":"","extra":null,"zero":0}}'
    out = json.loads(Sanitizer(DatasetContext("s")).sanitize_json(raw).content)
    assert out["cfdi"]["extra"] is None and out["cfdi"]["zero"] == 0 and out["cfdi"]["folio"]
    assert "sourceHash" not in out["metadata"]


def test_encrypted_mapping(tmp_path):
    pytest.importorskip("cryptography")
    context = DatasetContext("secret-seed"); expected = context.map("uuid", "real", lambda d: d.hex())
    path = tmp_path / "project.mapping.enc"; context.save_encrypted(path, "password")
    loaded = DatasetContext.load_encrypted(path, "password")
    assert loaded.map("uuid", "real", lambda d: "wrong") == expected
    assert b"real" not in path.read_bytes()


def test_batch_atomic_outputs_and_verify(tmp_path):
    output = tmp_path / "out"
    report = run(FIXTURE, output, "seed", Options())
    assert report["documentsExported"] == 1 and report["documentsBlocked"] == 0
    assert verify(output)["status"] == "PASS"
