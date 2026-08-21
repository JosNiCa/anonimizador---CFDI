from __future__ import annotations

import json
import secrets
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .batch import inspect, run_batch
from .models import Mode, Options
from .financial.models import DocumentType


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__(); self.title("CFDI Dataset Sanitizer"); self.geometry("760x520")
        self.source = tk.StringVar(); self.output = tk.StringVar(); self.mode = tk.StringVar(value="identity")
        self.sources: list[Path] = []
        self.detected_type = tk.StringVar(value="Tipo detectado: pendiente de análisis")
        self.document_type = tk.StringVar(value="AUTO")
        ttk.Label(self, text="CFDI Dataset Sanitizer", font=("TkDefaultFont", 18, "bold")).pack(pady=14)
        ttk.Label(self, text="Los archivos se procesan únicamente en este equipo.\nNo se realizan conexiones externas.", foreground="#075985").pack()
        form = ttk.Frame(self); form.pack(fill="x", padx=28, pady=18)
        self._row(form, "Archivo o carpeta", self.source, self._choose_source, 0)
        self._row(form, "Carpeta de salida", self.output, self._choose_output, 1)
        ttk.Label(form, text="Modo").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Radiobutton(form, text="Identidad sanitizada (recomendado)", variable=self.mode, value="identity").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(form, text="Sintético reforzado (transformación insegura se omite)", variable=self.mode, value="synthetic").grid(row=3, column=1, sticky="w")
        ttk.Label(form, textvariable=self.detected_type, foreground="#075985").grid(row=4, column=1, sticky="w", pady=8)
        ttk.Label(form, text="Tipo PDF").grid(row=5, column=0, sticky="w")
        ttk.Combobox(form, textvariable=self.document_type, state="readonly",
                     values=("AUTO", "BANK_STATEMENT", "TRIAL_BALANCE", "AUXILIARY_LEDGER")).grid(row=5, column=1, sticky="w")
        controls = ttk.Frame(self); controls.pack()
        ttk.Button(controls, text="Analizar", command=self._inspect).pack(side="left", padx=8)
        ttk.Button(controls, text="Sanitizar", command=self._sanitize).pack(side="left", padx=8)
        self.report = tk.Text(self, height=14, width=90, state="disabled"); self.report.pack(padx=24, pady=16)

    def _row(self, parent, label, variable, command, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=variable, width=62).grid(row=row, column=1, padx=8)
        ttk.Button(parent, text="Elegir…", command=command).grid(row=row, column=2)
    def _choose_source(self):
        selected = filedialog.askopenfilenames(
            title="Seleccionar lote de documentos",
            filetypes=[("Documentos", "*.xml *.json *.pdf")],
        )
        if selected:
            self.sources = [Path(path) for path in selected]
            summary = str(self.sources[0]) if len(self.sources) == 1 else f"{len(self.sources)} archivos seleccionados"
            self.source.set(summary)
            return
        directory = filedialog.askdirectory(title="O seleccionar una carpeta completa")
        if directory:
            self.sources = [Path(directory)]
            self.source.set(directory)
    def _choose_output(self): self.output.set(filedialog.askdirectory())
    def _show(self, value): self.report.configure(state="normal"); self.report.delete("1.0", "end"); self.report.insert("end", json.dumps(value, indent=2, ensure_ascii=False)); self.report.configure(state="disabled")
    def _inspect(self):
        try:
            if len(self._selected_sources()) != 1:
                raise ValueError("El análisis previo admite un documento a la vez")
            result = inspect(self._selected_sources()[0], self._forced_type())
            if "documentType" in result: self.detected_type.set(f"Tipo detectado: {result['documentType']}")
            self._show({"categorías detectadas (sin revelar valores)": result})
        except Exception as exc: messagebox.showerror("No se pudo analizar", str(exc))
    def _sanitize(self):
        try:
            mode = Mode.IDENTITY_ONLY if self.mode.get() == "identity" else Mode.SYNTHETIC_REINFORCED
            self._show(run_batch(self._selected_sources(), Path(self.output.get()),
                                 secrets.token_urlsafe(32), Options(mode),
                                 forced_type=self._forced_type()))
        except Exception as exc: messagebox.showerror("Exportación bloqueada", str(exc))

    def _selected_sources(self) -> list[Path]:
        if self.sources:
            return self.sources
        if self.source.get():
            return [Path(self.source.get())]
        raise ValueError("Seleccione al menos un archivo o carpeta")

    def _forced_type(self):
        return None if self.document_type.get() == "AUTO" else DocumentType(self.document_type.get())


def main() -> None: App().mainloop()
