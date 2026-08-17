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

