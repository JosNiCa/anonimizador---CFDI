# Modelo de amenazas

Se considera adversario a quien obtiene el dataset público o logs. Se protegen identificadores,
datos bancarios, contacto, timbre y metadatos correlacionables. Controles: procesamiento offline,
HMAC secreto, mapping cifrado, parser anti-XXE, nombres de salida neutros, escritura atómica y
escaneo residual. Riesgos restantes: equipo comprometido, contraseña débil, texto libre no
detectado y cuasi-identificadores económicos/temporales. No se afirma anonimato absoluto.

