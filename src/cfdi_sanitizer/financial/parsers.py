from __future__ import annotations

import re
from abc import ABC, abstractmethod

from .models import DocumentType, FinancialDocument, TextFragment

MONEY = re.compile(r"(?<![\w.])-?\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})(?!\w)")
ACCOUNT_CODE = re.compile(r"(?m)^\s*(\d{3}(?:\.\d{2})*)\b")


class FinancialDocumentParser(ABC):
    document_type: DocumentType

    @abstractmethod
    def parse(self, pages: list[str], metadata: dict[str, str]) -> FinancialDocument: ...

    def base(self, pages: list[str], metadata: dict[str, str]) -> FinancialDocument:
        text = "\n".join(pages)
        return FinancialDocument(
            document_type=self.document_type,
            pages=pages,
            metadata=metadata,
            fragments=[TextFragment(line, page) for page, body in enumerate(pages, 1) for line in body.splitlines()],
            financial_values=MONEY.findall(text),
            account_codes=ACCOUNT_CODE.findall(text),
        )


class TrialBalanceParser(FinancialDocumentParser):
    document_type = DocumentType.TRIAL_BALANCE

    def parse(self, pages: list[str], metadata: dict[str, str]) -> FinancialDocument:
        return self.base(pages, metadata)


class AuxiliaryLedgerParser(FinancialDocumentParser):
    document_type = DocumentType.AUXILIARY_LEDGER

    def parse(self, pages: list[str], metadata: dict[str, str]) -> FinancialDocument:
        document = self.base(pages, metadata)
        document.movement_count = sum(bool(re.match(r"\s*\w+\s+\d+\s+\d{2}[/-]\d{2}", line)) for line in document.text.splitlines())
        return document


class BankStatementParser(FinancialDocumentParser):
    document_type = DocumentType.BANK_STATEMENT

    def parse(self, pages: list[str], metadata: dict[str, str]) -> FinancialDocument:
        document = self.base(pages, metadata)
        document.movement_count = sum(bool(re.match(r"\s*\d{2}[/-]\d{2}", line)) for line in document.text.splitlines())
        return document


PARSERS = {parser.document_type: parser for parser in (TrialBalanceParser(), AuxiliaryLedgerParser(), BankStatementParser())}

