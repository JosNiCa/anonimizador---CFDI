"""Punto de entrada estable para empaquetar la CLI con PyInstaller."""

from cfdi_sanitizer.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
