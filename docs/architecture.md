# Arquitectura

`batch` procesa un documento por vez. `core` analiza XML con `defusedxml` o JSON estándar,
consulta `policy`, usa `DatasetContext` HMAC y generadores, valida ausencia de originales y entrega
bytes a escritura atómica. XML genera su proyección JSON con el mismo árbol ya transformado, por
lo que ambas salidas representan la misma identidad. `cli` y `ui` son adaptadores sin lógica de
privacidad. No existe componente de red.

El mapping efímero sólo reside en RAM. La persistencia opcional (`*.mapping.enc`) cifra semilla y
tabla con Fernet, derivando clave mediante PBKDF2; sólo ese archivo puede contener valores reales.
Nunca se copia al directorio de salida ni aparece en manifest o logs.

