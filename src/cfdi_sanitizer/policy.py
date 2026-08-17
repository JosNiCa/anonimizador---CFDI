POLICY = {
    "rfc": "rfc", "nombre": "name", "razonsocial": "name", "uuid": "uuid",
    "email": "email", "correo": "email", "telefono": "phone", "phone": "phone",
    "clabe": "account", "cuenta": "account", "account": "account",
    "folio": "identifier", "referencia": "identifier", "reference": "identifier",
    "pedido": "identifier", "order": "identifier", "contrato": "identifier",
    "customerid": "identifier", "providerid": "identifier", "employeeid": "identifier",
    "documentid": "identifier", "sourcehash": "remove", "sello": "neutralize",
    "sellocfd": "neutralize", "sellosat": "neutralize", "certificado": "neutralize",
    "nocertificado": "neutralize", "nocertificadosat": "neutralize",
    "domicilio": "address", "direccion": "address", "codigopostal": "postal",
    "domiciliofiscalreceptor": "postal", "curp": "identifier",
}
SENSITIVE_HINTS = tuple(POLICY)

FINANCIAL_DOCUMENT_POLICY = {
    "organization_name": "pseudonymize:name", "rfc": "pseudonymize:rfc",
    "client_number": "pseudonymize:identifier", "bank_account": "pseudonymize:account",
    "clabe": "pseudonymize:clabe", "counterparty": "pseudonymize:name",
    "tracking_key": "pseudonymize:identifier", "reference": "pseudonymize:identifier",
    "transaction_number": "pseudonymize:identifier", "account_code": "preserve",
    "generic_account_name": "preserve", "bank_name": "preserve",
    "amount": "preserve", "balance": "preserve", "currency": "preserve", "date": "policy",
    "anonymize_financial_institutions": False,
}
