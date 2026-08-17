from __future__ import annotations

import pytest

from cfdi_sanitizer.core import Sanitizer
from cfdi_sanitizer.financial.detection import detect_sensitive
from cfdi_sanitizer.financial.detector import detect_document_type
from cfdi_sanitizer.financial.models import DocumentType
from cfdi_sanitizer.financial.parsers import PARSERS
from cfdi_sanitizer.financial.service import FinancialDocumentSanitizer
from cfdi_sanitizer.financial.validation import validate_preservation
from cfdi_sanitizer.mapping import DatasetContext

BANK = """ESTADO DE CUENTA
BANCO DEMOSTRACION
RAZON SOCIAL: EMPRESA DEMO SA DE CV
RFC: CDE900101XY0
CLIENTE: 778899
CUENTA: 0451239087
CLABE: 012450004512390871
SALDO INICIAL 18,450.30 DEPOSITOS 64,000.00 RETIROS 58,612.00 SALDO FINAL 23,838.30
01/02/2026 COMPRA ORDEN DE PAGO SPEI 3,200.00 20,000.00
BENEF: PROVEEDORA DEL NORTE SA DE CV
PAGO FACTURA 1102
CVE RASTREO: 8846APR2202602034833547482
RFC: PIG910304LK2
"""

TRIAL_BAD = """BALANZA DE COMPROBACION EJERCICIO 2026 PERIODO 01
RAZON SOCIAL: EMPRESA DEMO SA DE CV
RFC: CDE900101XY0
CUENTA SALDO INICIAL DEBE HABER SALDO FINAL
102 Bancos 0.00 65,000.00 70,000.00 -5,000.00
102.01 Bancos nacionales 0.00 65,000.00 70,000.00 -5,000.00
102.01.01 BBVA 0.00 30,000.00 35,000.00 -5,000.00
102.01.02 SANTANDER 0.00 35,000.00 35,000.00 0.00
201.01.01 PROVEEDORA DEL NORTE SA DE CV 0.00 0.00 0.00 0.00
TOTAL 0.00 65,000.00 70,000.00 -5,000.00
"""

AUXILIARY = """REPORTE DE AUXILIARES
RAZON SOCIAL: EMPRESA DEMO SA DE CV
RFC: CDE900101XY0
PERIODO 01/01/2026 - 31/01/2026
CUENTA 105.01 CLIENTES SALDO INICIAL 5,000.00
TIPO NUMERO FECHA CONCEPTO DEBE HABER SALDO
DIARIO 1001 05/01/2026 Cobro cliente PROVEEDORA DEL NORTE SA DE CV factura 340 3,200.00 0.00 8,200.00
TOTAL 3,200.00 0.00 8,200.00
"""


def parse(text: str, kind: DocumentType):
    document = PARSERS[kind].parse([text], {})
    detect_sensitive(document)
    return document


def sanitize_text(text: str, kind: DocumentType, context: DatasetContext) -> str:
    service = FinancialDocumentSanitizer(context)
    document = parse(text, kind)
    for occurrence in document.occurrences:
        occurrence.replacement = service._replacement(occurrence.kind, occurrence.value)
    return service._replace_page(text, 1, document.occurrences)


@pytest.mark.parametrize("text,expected", [(BANK, DocumentType.BANK_STATEMENT), (TRIAL_BAD, DocumentType.TRIAL_BALANCE), (AUXILIARY, DocumentType.AUXILIARY_LEDGER)])
def test_document_type_detection(text, expected):
    assert detect_document_type(text) is expected


def test_bank_identity_changes_but_financial_semantics_remain():
    output = sanitize_text(BANK, DocumentType.BANK_STATEMENT, DatasetContext("dataset"))
    for original in ("CDE900101XY0", "0451239087", "012450004512390871", "PIG910304LK2", "PROVEEDORA DEL NORTE SA DE CV"):
        assert original not in output
    for preserved in ("COMPRA ORDEN DE PAGO SPEI", "PAGO FACTURA", "18,450.30", "64,000.00", "58,612.00", "23,838.30"):
        assert preserved in output


def test_unbalanced_trial_balance_and_hierarchy_are_preserved():
    original = parse(TRIAL_BAD, DocumentType.TRIAL_BALANCE)
    output = sanitize_text(TRIAL_BAD, DocumentType.TRIAL_BALANCE, DatasetContext("dataset"))
    sanitized = parse(output, DocumentType.TRIAL_BALANCE)
    validate_preservation(original, sanitized)
    assert sanitized.account_codes == ["102", "102.01", "102.01.01", "102.01.02", "201.01.01"]
    assert "65,000.00" in output and "70,000.00" in output
    assert "201.01.01" in output and "PROVEEDORA DEL NORTE SA DE CV" not in output


def test_balanced_trial_balance_remains_balanced():
    balanced = TRIAL_BAD.replace("65,000.00", "70,000.00")
    original = parse(balanced, DocumentType.TRIAL_BALANCE)
    output = sanitize_text(balanced, DocumentType.TRIAL_BALANCE, DatasetContext("dataset"))
    validate_preservation(original, parse(output, DocumentType.TRIAL_BALANCE))
    assert output.count("70,000.00") == balanced.count("70,000.00")


def test_auxiliary_preserves_movement_and_amounts():
    original = parse(AUXILIARY, DocumentType.AUXILIARY_LEDGER)
    output = sanitize_text(AUXILIARY, DocumentType.AUXILIARY_LEDGER, DatasetContext("dataset"))
    sanitized = parse(output, DocumentType.AUXILIARY_LEDGER)
    validate_preservation(original, sanitized)
    assert "Cobro cliente" in output and "factura" in output
    assert "3,200.00" in output and "8,200.00" in output and " 340 " not in output


def test_cross_document_entity_mapping_with_cfdi():
    context = DatasetContext("shared")
    cfdi = b'''<x:Comprobante xmlns:x="http://www.sat.gob.mx/cfd/4" Version="4.0"><x:Emisor Rfc="AAA010101AAA" Nombre="PROVEEDORA DEL NORTE SA DE CV"/></x:Comprobante>'''
    cfdi_output = Sanitizer(context).sanitize_xml(cfdi).content.decode()
    outputs = [sanitize_text(text, kind, context) for text, kind in ((BANK, DocumentType.BANK_STATEMENT), (TRIAL_BAD, DocumentType.TRIAL_BALANCE), (AUXILIARY, DocumentType.AUXILIARY_LEDGER))]
    synthetic = context.map("name", "PROVEEDORA DEL NORTE SA DE CV", lambda _: "unexpected")
    assert synthetic in cfdi_output and all(synthetic in output for output in outputs)


def test_name_and_rfc_are_linked_as_one_entity():
    context = DatasetContext("shared")
    entity = context.link_entity("EMPRESA DEMO SA DE CV", "CDE900101XY0")
    assert entity == context.link_entity("EMPRESA DEMO SA DE CV", "CDE900101XY0")
    assert context._entity_links["name:EMPRESA DEMO SA DE CV"] == context._entity_links["rfc:CDE900101XY0"]


def test_pdf_is_reconstructed_and_residual_text_is_absent():
    pytest.importorskip("pypdf"); pytest.importorskip("reportlab")
    from cfdi_sanitizer.financial.pdf import extract_pdf, render_clean_pdf
    original_pdf = render_clean_pdf([BANK], "MUESTRA SINTETICA")
    result = FinancialDocumentSanitizer(DatasetContext("dataset")).sanitize(original_pdf)
    text = "\n".join(extract_pdf(result.content)[0])
    assert "CDE900101XY0" not in text and "012450004512390871" not in text
    assert "18,450.30" in text and "SIN VALIDEZ DOCUMENTAL / FISCAL" in text
    assert b"CDE900101XY0" not in result.content
    assert result.financial_preservation == "PASS"
