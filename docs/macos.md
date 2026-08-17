# Ejecutar CFDI Dataset Sanitizer en macOS

Esta guía aplica tanto a equipos Apple Silicon (`arm64`, por ejemplo M1–M4) como Intel (`x86_64`).
El procesamiento sigue siendo completamente local: ejecutar la aplicación no consulta al SAT, no
envía telemetría y no requiere Internet una vez instaladas sus dependencias.

## Opción 1: ejecutar desde el código fuente

### 1. Comprobar Python y Tkinter

Abra **Terminal** y ejecute:

```bash
python3 --version
python3 -m tkinter
```

Se requiere Python 3.11 o posterior. El segundo comando debe abrir una pequeña ventana de prueba;
ciérrela para continuar. Si macOS no tiene una versión compatible, instale el paquete universal de
Python 3.11+ desde `python.org`. Ese instalador incluye Tkinter. La instalación necesita Internet
una sola vez, pero la sanitización posterior no utiliza la red.

### 2. Crear un entorno aislado

Cambie `/ruta/al/anonimizador---CFDI` por la carpeta donde descargó el proyecto:

```bash
cd /ruta/al/anonimizador---CFDI
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Cuando el entorno está activo, Terminal muestra normalmente `(.venv)` al inicio de la línea. No
use `sudo pip`: el entorno virtual mantiene las dependencias dentro de la carpeta del proyecto.

### 3. Abrir la interfaz gráfica

```bash
cfdi-sanitizer-gui
```

En la ventana:

1. Pulse **Elegir…** para seleccionar un XML o JSON.
2. Elija una carpeta de salida distinta de la carpeta del original.
3. Mantenga **Identidad sanitizada** para conservar cantidades e importes.
4. Pulse **Analizar** para revisar categorías sin mostrar sus valores.
5. Pulse **Sanitizar**. Sólo los documentos aprobados se escribirán en la salida.

Para abrir la aplicación en otra sesión de Terminal:

```bash
cd /ruta/al/anonimizador---CFDI
source .venv/bin/activate
cfdi-sanitizer-gui
```

Para salir del entorno virtual después de cerrar la aplicación, ejecute `deactivate`.

## Usar la línea de comandos en macOS

Con `.venv` activado:

```bash
# Analiza categorías sin revelar los datos completos
cfdi-sanitizer inspect /ruta/a/factura.xml

# Simula un lote sin escribir documentos sanitizados
cfdi-sanitizer sanitize /ruta/a/entrada \
  --output /ruta/a/salida \
  --mode identity \
  --seed 'secreto-largo-y-privado' \
  --dry-run

# Sanitiza el lote y verifica el resultado
cfdi-sanitizer sanitize /ruta/a/entrada \
  --output /ruta/a/salida \
  --mode identity \
  --seed 'secreto-largo-y-privado'
cfdi-sanitizer verify /ruta/a/salida
```

No guarde la semilla en el directorio exportado ni la comparta con el dataset. Para obtener las
mismas identidades ficticias en lotes posteriores debe reutilizar exactamente la misma semilla.

## Opción 2: construir una aplicación `.app` autocontenida

La compilación debe realizarse **en macOS** y para la arquitectura que se distribuirá. Apple
Silicon e Intel requieren artefactos separados, salvo que el equipo de distribución configure un
build universal y todas las dependencias lo soporten.

```bash
cd /ruta/al/anonimizador---CFDI
source .venv/bin/activate
python -m pip install -e '.[dev]'
pyinstaller --clean --noconfirm --windowed \
  --name CFDI-Dataset-Sanitizer \
  --paths src \
  packaging/gui_launcher.py
open dist/CFDI-Dataset-Sanitizer.app
```

El resultado queda en `dist/CFDI-Dataset-Sanitizer.app`. Para entregarlo a otras personas, el
responsable de distribución debe firmarlo con un certificado **Developer ID Application** y
notarizarlo con Apple. Un build local sin firma puede abrirse para pruebas con clic secundario sobre
la aplicación, **Abrir**, y confirmando **Abrir**; no se recomienda desactivar Gatekeeper de forma
global.

Ejemplo para crear además el ejecutable de terminal:

```bash
pyinstaller --clean --noconfirm \
  --name cfdi-sanitizer \
  --paths src \
  packaging/cli_launcher.py
./dist/cfdi-sanitizer --help
```

## Solución de problemas

- **`command not found: cfdi-sanitizer-gui`**: active primero el entorno con
  `source .venv/bin/activate` y repita `python -m pip install -e .`.
- **`No module named tkinter`**: use el instalador oficial de Python para macOS que incluye
  Tkinter y vuelva a crear `.venv` con esa versión.
- **La carpeta de salida es rechazada**: seleccione una ubicación distinta de la del original; la
  aplicación nunca sobrescribe documentos de entrada.
- **Gatekeeper bloquea el `.app`**: para un build interno sin firma use clic secundario → **Abrir**.
  Para distribución a clientes, firme y notarice el artefacto.
- **El resultado fue bloqueado**: consulte el reporte. Por seguridad, un documento con información
  original residual conocida no se exporta.

