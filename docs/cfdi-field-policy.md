# Política por campo

| Campo | Clasificación | Acción | Razón | Método |
|---|---|---|---|---|
| Rfc Emisor/Receptor/Tercero | IDENTIFICADOR | PSEUDONYMIZE | Identifica contribuyente | RFC sintético HMAC |
| Nombre/Razón social | IDENTIFICADOR | PSEUDONYMIZE | Identidad directa | Nombre sintético HMAC |
| UUID/relacionado | IDENTIFICADOR | PSEUDONYMIZE | Correlación fiscal | UUID v4 sintético HMAC compartido |
| Sello/Certificado/Número | CRIPTOGRÁFICO | NEUTRALIZE | Vincula original | Marcador no fiscal |
| Email/Teléfono/Cuenta/CLABE | PII | PSEUDONYMIZE | Contacto/finanzas | Namespace sintético HMAC |
| Domicilio/CP | PII | GENERALIZE | Localización | Dirección sintética / 00000 |
| Folio/Referencia/Pedido | IDENTIFICADOR | PSEUDONYMIZE | Correlación interna | `SYN-*` HMAC |
| Regímenes/UsoCFDI/FormaPago | CATÁLOGO | PRESERVE | Valor analítico | Sin cambios |
| Cantidad/Importe/Impuestos | ECONÓMICO | PRESERVE V1 | Preservar anomalías | Decimal textual intacto |
| Campo desconocido sospechoso | DESCONOCIDO | WARN/SCAN | Privacidad conservadora | Heurística y bloqueo residual |

