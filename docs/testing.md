# Pruebas

`pytest` cubre determinismo, RFC/UUID compartidos, relaciones interdocumento, XML/JSON, anti-XXE,
fechas, preservación de tipos, mapping cifrado, lote atómico y verificación. Fixtures son totalmente
sintéticos. `ruff check .` ejecuta lint; `mypy src` revisa tipos.

`test_financial.py` prueba detección de las tres familias, estado de cuenta, semántica SPEI, balanza
incorrecta 65.000/70.000, jerarquía, auxiliar, consistencia de entidad con CFDI y reextracción
residual del PDF reconstruido. La integración PDF requiere las dependencias declaradas pypdf y
ReportLab; todos los textos de prueba son ficticios.
