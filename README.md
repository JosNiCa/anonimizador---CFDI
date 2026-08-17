# CFDI Dataset Sanitizer

Aplicación local, auditable y determinista para pseudonimizar CFDI 4.0 XML y el contrato JSON
canónico del proyecto. Produce XML/JSON correlacionados, neutraliza material criptográfico,
conserva estructura económica y bloquea resultados con PII original residual conocida.

> **Los documentos generados por esta herramienta han sido modificados deliberadamente y no
> deben utilizarse como comprobantes fiscales ni como sustitutos del CFDI original.**

## Privacidad y alcance

- Procesa todo en el equipo: **cero conexiones de red**, APIs, IA, telemetría o consultas al SAT.
- No corrige CFDI ni promete anonimato absoluto o validez fiscal. Preserva anomalías originales.
- La semilla HMAC mantiene identidades coherentes. Sin `--seed` se crea una semilla efímera.
- Un proyecto persistente puede guardarse cifrado con Fernet y PBKDF2-HMAC-SHA256 (600.000
  iteraciones); el mapping jamás acompaña al dataset.
- Fechas e importes particulares, descripciones y combinaciones raras pueden permitir
  reidentificación indirecta. Revise las advertencias antes de publicar.

## Instalación y ejecución

```bash
python -m venv .venv
. .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cfdi-sanitizer inspect factura.xml
cfdi-sanitizer sanitize ./input --output ./dataset --mode identity --seed 'secreto-largo'
cfdi-sanitizer sanitize ./input --output ./dataset --dry-run
cfdi-sanitizer verify ./dataset
cfdi-sanitizer-gui
pytest
```

La GUI permite elegir archivo, salida, analizar categorías sin mostrar valores y sanitizar. El
modo `identity` conserva dinero. En `synthetic`, V1 aplica la política conservadora
`SKIPPED_UNSAFE_TRANSFORMATION` y mantiene importes si no demuestra coherencia completa.

## Formatos, salida y seguridad

El XML CFDI 4.0 es fuente fiscal y se reconoce por URI, no por prefijo. Por cada XML se genera
XML y JSON canónico (`metadata`, `cfdi`); JSON de entrada conserva objetos, arrays, `null`, tipos,
ausencias y extras. Se añade `datasetSanitization`, comentario XML y manifest no sensible. Los
nombres de salida son `DOC-000001`, evitando filtrar nombres privados. La escritura es atómica y
se rechaza usar la ubicación original como salida.

Material `Sello`, certificados y equivalentes se neutraliza; UUID/RFC/identidades se reemplazan
mediante HMAC. DTD y declaraciones de entidades se rechazan antes del parseo para impedir XXE. No
hay código de red.

## Desarrollo, pruebas y distribución

Arquitectura: `input → parser seguro → política → mapping → transformación → validación → scan
residual → escritura atómica`. Consulte [`docs/architecture.md`](docs/architecture.md).

```bash
ruff check .
mypy src
pytest
pyinstaller --windowed --name CFDI-Dataset-Sanitizer src/cfdi_sanitizer/ui.py
pyinstaller --name cfdi-sanitizer src/cfdi_sanitizer/cli.py
```

PyInstaller genera binarios autocontenidos por plataforma; cada artefacto debe compilarse y
firmarse en Windows, macOS y Linux respectivamente. No se requiere Docker ni Python en el equipo
del cliente.

## Limitaciones V1

- Sólo CFDI 4.0; validación XSD local aún no se integra.
- El JSON no tiene estándar SAT: se preserva el contrato encontrado y XML se proyecta al contrato
  canónico documentado.
- El escáner determinista no comprende semántica libre; campos desconocidos sensibles producen
  advertencias y los originales ya mapeados bloquean la exportación.
- Montos sintéticos se omiten conservadoramente; no se implementa el motor fiscal completo de
  complementos de pagos, nómina, comercio exterior o impuestos locales.
- Drag & drop y gestión de contraseña de proyecto no están expuestos aún en la GUI básica.
