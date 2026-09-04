"""
Descubrimiento automático de la estructura del corpus (Fase 0/1).

NO asume una estructura de carpetas fija. Camina recursivamente
`corpus_path`, clasifica cada archivo por extensión, e infiere
fenómeno/observatorio comparando los componentes de la ruta contra
los códigos/nombres conocidos del índice oficial (config.yaml).

Si un archivo no puede mapearse a un observatorio conocido, se marca
como `fenomeno=UNKNOWN` / `observatorio=UNKNOWN` y se reporta -- nunca
se descarta silenciosamente ni se le asigna un fenómeno inventado.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional

from src.utils.io import file_hash, stable_id
from src.utils.logging import get_logger

log = get_logger("ingestion.discover")


@dataclass
class DiscoveredFile:
    path: str                 # ruta absoluta real (para lectura)
    rel_path: str              # ruta relativa a corpus_path (para reproducibilidad/reporte)
    filename: str
    extension: str             # con punto, en minúsculas, p.ej. ".pdf"
    formato: str                # categoría lógica: pdf/json/csv/excel/imagen/texto/pbf/otro
    fenomeno: str               # F1/F2/F3/UNKNOWN
    observatorio: str          # código del observatorio o UNKNOWN
    size_bytes: int
    doc_id: str = field(default="")
    is_empty: bool = False

    def __post_init__(self):
        if not self.doc_id:
            # Determinístico y estable: basado en observatorio + ruta relativa.
            self.doc_id = f"{self.observatorio}_{stable_id(self.rel_path)}"


def _build_observatorio_lookup(cfg: dict) -> dict[str, tuple[str, str]]:
    """Devuelve {token_normalizado: (fenomeno, codigo_observatorio)}.

    Incluye tanto el código (p.ej. 'SWF') como el nombre de carpeta esperado
    (p.ej. 'SWF_Counterspace'), normalizados en minúsculas.
    """
    lookup: dict[str, tuple[str, str]] = {}
    for fenomeno, observatorios in cfg.get("observatorios", {}).items():
        for obs in observatorios:
            codigo = obs["codigo"]
            nombre = obs["nombre"]
            lookup[codigo.lower()] = (fenomeno, codigo)
            lookup[nombre.lower()] = (fenomeno, codigo)
    return lookup


def _infer_fenomeno_observatorio(
    rel_path: Path, lookup: dict[str, tuple[str, str]]
) -> tuple[str, str]:
    """Busca en cada componente de la ruta relativa un match contra el lookup.

    Estrategia: match exacto de componente primero (rápido y seguro);
    si no hay match exacto, intenta contención de substring (p.ej. carpeta
    'F1_AIINDEX_docs' contiene 'aiindex').
    """
    parts = [p.lower() for p in rel_path.parts[:-1]]  # excluye el nombre de archivo

    # 1) match exacto de componente
    for part in parts:
        if part in lookup:
            return lookup[part]

    # 2) match por fenómeno explícito tipo "F1", "F2", "F3" en el nombre de carpeta
    fenomeno_directo = None
    for part in parts:
        for fcode in ("f1", "f2", "f3"):
            if part == fcode or part.startswith(fcode + "_") or part.startswith(fcode + "-"):
                fenomeno_directo = fcode.upper()

    # 3) substring contention contra observatorios conocidos
    for part in parts:
        for key, val in lookup.items():
            if key in part or part in key:
                fenomeno, codigo = val
                return fenomeno, codigo

    if fenomeno_directo:
        return fenomeno_directo, "UNKNOWN"

    return "UNKNOWN", "UNKNOWN"


EXTENSION_MAP_DEFAULT = {
    ".pdf": "pdf",
    ".json": "json",
    ".csv": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".jpg": "imagen",
    ".jpeg": "imagen",
    ".png": "imagen",
    ".txt": "texto",
    ".pbf": "pbf",
}


def discover_corpus(
    corpus_path: str | Path,
    cfg: dict,
    compute_hash: bool = False,
) -> Iterator[DiscoveredFile]:
    """Camina el corpus de forma recursiva e incremental (generador, no lista).

    No carga contenido de archivos en memoria -- solo metadata de filesystem
    (y opcionalmente hash, que sí lee el archivo mediante streaming).
    """
    corpus_path = Path(corpus_path)
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"corpus_path no existe: {corpus_path}. "
            "Verifica config.yaml -> paths.corpus_path."
        )

    ext_map = cfg.get("audit", {}).get("extension_map", EXTENSION_MAP_DEFAULT)
    lookup = _build_observatorio_lookup(cfg)

    n_seen = 0
    for root, dirs, files in os.walk(corpus_path):
        # ignora carpetas ocultas / de sistema
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fname in files:
            if fname.startswith("."):
                    continue
            abs_path = Path(root) / fname
            
            # Convierte abs_path al formato de ruta extendida en Windows para superar el límite de 260 caracteres
            abs_path_str = str(abs_path)
            if os.name == "nt" and not abs_path_str.startswith("\\\\?\\"):
                abs_path_str = "\\\\?\\" + os.path.abspath(abs_path_str)

            try:
                size = os.path.getsize(abs_path_str)
            except OSError as e:
                log.warning(f"No se pudo hacer stat() de {abs_path}: {e}")
                continue

            # Normaliza la ruta relativa con "/" (as_posix) para compatibilidad multiplataforma
            rel_path = abs_path.relative_to(corpus_path).as_posix()
            ext = abs_path.suffix.lower()
            formato = ext_map.get(ext, "otro")
            fenomeno, observatorio = _infer_fenomeno_observatorio(Path(rel_path), lookup)

            df = DiscoveredFile(
                path=str(abs_path),
                rel_path=rel_path,
                filename=fname,
                extension=ext,
                formato=formato,
                fenomeno=fenomeno,
                observatorio=observatorio,
                size_bytes=size,
                is_empty=(size == 0),
            )
            n_seen += 1
            yield df

    log.info(f"discover_corpus: {n_seen} archivos descubiertos bajo {corpus_path}")