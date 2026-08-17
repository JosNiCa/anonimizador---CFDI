# Decisiones

1. No había archivos ni contrato previo en el repositorio; se adoptó el contrato conceptual del
   encargo para la proyección XML, preservando JSON de entrada sin normalizar.
2. Transformación económica reforzada se omite en V1 (`SKIPPED_UNSAFE_TRANSFORMATION`) porque no
   puede demostrarse segura para todos los complementos. Privacidad de identidad sí se aplica.
3. Campos desconocidos se preservan para no destruir valor; nombres sospechosos generan advertencia
   y patrones/originales conocidos se escanean antes de exportar.

