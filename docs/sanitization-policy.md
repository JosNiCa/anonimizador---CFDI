# Política de sanitización 1.0.0

La tabla auditable vive en `src/cfdi_sanitizer/policy.py`. Identificadores se pseudonimizan con
HMAC-SHA256; sellos/certificados se neutralizan; catálogos e importes se preservan. Fechas permiten
KEEP, SHIFT global fijo o GENERALIZE. Texto libre se inspecciona por patrones. Un original conocido
residual bloquea el documento. Sanitizar no significa corregir.

