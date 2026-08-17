"""
Utilidades de I/O compartidas.

CRÍTICO (regla #25 / #37 del reto): ninguna ruta debe ser absoluta ni depender
del directorio desde el que se invoque el script. `PROJECT_ROOT` se resuelve
de forma robusta a partir de la ubicación de este archivo, no del cwd.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

# src/utils/io.py -> src/utils -> src -> <project_root>
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(relative_or_absolute: str | Path) -> Path:
    """Resuelve una ruta del config.yaml relativa a PROJECT_ROOT.

    Si ya es absoluta, se respeta tal cual (permite overrides explícitos),
    pero el config.yaml del repo NUNCA debe traer rutas absolutas por defecto.
    """
    p = Path(relative_or_absolute)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def load_config(config_path: str | Path | None = None) -> dict:
    """Carga config.yaml. Por defecto busca <PROJECT_ROOT>/config.yaml."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"No se encontró config.yaml en {config_path}. "
            f"PROJECT_ROOT resuelto = {PROJECT_ROOT}"
        )
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_jsonl(path: str | Path) -> Iterator[dict]:
    path = Path(path)
    if not path.exists():
        return
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSONL inválido en {path}:{line_num}: {e}") from e


def write_jsonl(path: str | Path, records: Iterable[dict], mode: str = "w") -> int:
    path = Path(path)
    ensure_dir(path.parent)
    count = 0
    with open(path, mode, encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")
            count += 1
    return count


def append_jsonl(path: str | Path, record: dict) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False))
        f.write("\n")


def file_hash(path: str | Path, chunk_bytes: int = 1024 * 1024) -> str:
    """SHA-256 incremental (no carga el archivo completo en memoria)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk_bytes)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(*parts: Any) -> str:
    """Genera un ID corto (12 hex) estable y reproducible a partir de partes."""
    joined = "||".join(str(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def detect_encoding_guess(path: str | Path, sample_bytes: int = 65536) -> str:
    """Heurística ligera de encoding sin dependencias pesadas.

    Intenta utf-8 estricto; si falla, cae a latin-1 (siempre decodifica,
    aunque puede introducir mojibake que se reporta en la auditoría).
    """
    with open(path, "rb") as f:
        sample = f.read(sample_bytes)
    try:
        sample.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        sample.decode("cp1252")
        return "cp1252"
    except UnicodeDecodeError:
        return "latin-1"  # latin-1 nunca falla (mapea 1:1 byte->codepoint)
