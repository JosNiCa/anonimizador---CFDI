# Documentos financieros PDF

## Estrategia de privacidad

Se eligieron **pypdf** para lectura/extracción estricta y **ReportLab** para reconstrucción. No se
redacta visualmente el original: el renderer crea páginas nuevas exclusivamente a partir del texto
ya transformado. Por diseño no copia content streams, XMP, metadata privada, attachments,
anotaciones, formularios, JavaScript ni capas del original. Luego pypdf extrae nuevamente todo el
texto del resultado; cualquier valor original conocido residual bloquea la exportación.

Esta estrategia prioriza privacidad y legibilidad sobre fidelidad pixel-perfect. Un PDF sin texto
extraíble produce `SCANNED_OR_IMAGE_PDF:OCR_REQUIRED`. `OCRProvider` define la extensión futura,
pero no existe implementación cloud ni llamada de red.

## Flujo

```text
PDF → extracción segura → detección determinista → parser de dominio
    → ocurrencias sensibles → DatasetContext HMAC compartido
    → sustitución semántica → validación de invariantes → PDF nuevo
    → reextracción → scan residual → sidecar/manifest o bloqueo
```

El modelo intermedio conserva tipo, páginas, fragmentos, metadata, importes, códigos contables,
movimientos y ocurrencias con página, contexto en memoria y bounding box cuando esté disponible.
Los valores/contextos originales nunca se escriben en sidecars, manifest o logs.

## Política por familia

| Familia | Pseudonimiza | Preserva |
|---|---|---|
| Estado de cuenta | titular, RFC, cliente, cuenta, CLABE, contraparte, rastreo, referencia, factura | banco, moneda, fechas, SPEI, depósito/retiro, saldos, comisiones e IVA |
| Balanza | empresa, RFC y entidades reales usadas como subcuenta | códigos, jerarquía, orden, nombres genéricos, Debe, Haber y saldos reportados |
| Auxiliar | empresa, RFC, cliente/proveedor, factura/ticket/póliza y número de movimiento | periodo, códigos, concepto financiero, fechas, Debe, Haber, saldo, orden y totales |

Los nombres bancarios y nombres contables genéricos se conservan. La política auditable
`FINANCIAL_DOCUMENT_POLICY` deja `account_code=preserve`, importes/saldos/moneda en `preserve`,
números de movimiento en `pseudonymize` y bancos sin anonimizar de forma predeterminada.

## Preservación financiera

El validador compara el multiconjunto textual de importes, la secuencia de códigos contables y el
número de movimientos antes/después. No exige que una balanza cuadre ni recalcula saldos: conserva
la anomalía original. En modo sintético reforzado, los importes PDF siguen sin modificarse hasta
que exista un transformador capaz de demostrar todas las relaciones por familia.

## Limitaciones

- La reconstrucción conserva páginas, líneas y orden, pero no tipografías ni coordenadas exactas.
- Tablas extraídas en orden incorrecto, ligaduras no recuperables o columnas sin etiquetas pueden
  requerir revisión manual.
- La detección de organizaciones es contextual y conservadora; una confianza insuficiente bloquea
  mediante `DOCUMENT_REQUIRES_MANUAL_REVIEW`.
- No hay OCR en V1. Imágenes escaneadas, firmas dibujadas y texto rasterizado requieren un proveedor
  OCR local futuro.
- Archivos cifrados se rechazan y objetos interactivos nunca se copian.
