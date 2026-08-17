"""
scripts/audit_lib.py

Lógica de auditoría incremental del corpus (usada por scripts/01_audit_corpus.py
y por los tests en tests/test_audit.py). Genera:
  reports/corpus_audit.json
  reports/corpus_audit.csv
  reports/corpus_summary.md

Diseño:
  - Procesamiento incremental (streaming), no carga el corpus en RAM.
  - Detecta: vacíos, duplicados (hash), corruptos (magic bytes / parseabilidad),
    problemas de encoding, distribución por extensión/fenómeno/observatorio/carpeta.
  - El conteo de tokens es una ESTIMACIÓN barata (whitespace-split) solo para
    formatos de texto plano ligero (txt/csv/json pequeños). Para PDF/XLSX el
    conteo real de tokens se calcula en la fase de extracción (02_extract.py),
    no aquí -- se reporta como "pendiente_extraccion".
  - Nunca falla silenciosamente: cada archivo problemático se registra en
    reports/errors.jsonl y el pipeline continúa con el resto.
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from src.ingestion.discover import discover_corpus
from src.utils.io import append_jsonl, ensure_dir, file_hash
from src.utils.logging import get_logger

log = get_logger("audit_corpus")

LARGE_FILE_SKIP_TOKEN_ESTIMATE = 20 * 1024 * 1024  # 20MB: no leer completo para estimar tokens


def _check_json_valid(path: Path) -> tuple[bool, str | None]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, None
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="latin-1") as f:
                json.load(f)
            return True, "leido_con_latin-1_no_utf8"
        except Exception as e:
            return False, f"json_invalido_encoding: {e}"
    except json.JSONDecodeError as e:
        return False, f"json_invalido: {e}"
    except Exception as e:
        return False, f"error_lectura: {e}"


def _check_pdf_valid(path: Path) -> tuple[bool, str | None]:
    try:
        with open(path, "rb") as f:
            header = f.read(5)
        if header != b"%PDF-":
            return False, "magic_bytes_invalidos_no_es_pdf"
        return True, None
    except Exception as e:
        return False, f"error_lectura: {e}"


def _check_xlsx_valid(path: Path) -> tuple[bool, str | None]:
    try:
        with open(path, "rb") as f:
            header = f.read(4)
        # XLSX es un ZIP: firma PK\x03\x04
        if header[:2] != b"PK":
            return False, "magic_bytes_invalidos_no_es_zip_xlsx"
        return True, None
    except Exception as e:
        return False, f"error_lectura: {e}"


def _check_image_valid(path: Path) -> tuple[bool, str | None]:
    try:
        with open(path, "rb") as f:
            header = f.read(8)
        is_jpg = header[:2] == b"\xff\xd8"
        is_png = header[:8] == b"\x89PNG\r\n\x1a\n"
        if not (is_jpg or is_png):
            return False, "magic_bytes_invalidos_no_es_jpg_ni_png"
        return True, None
    except Exception as e:
        return False, f"error_lectura: {e}"


def _check_csv_valid(path: Path, encoding: str) -> tuple[bool, str | None]:
    try:
        with open(path, "r", encoding=encoding, newline="") as f:
            sample = f.read(8192)
        if not sample.strip():
            return False, "csv_vacio_o_solo_whitespace"
        try:
            csv.Sniffer().sniff(sample)
        except csv.Error:
            # No siempre es fatal (CSV de una sola columna), se reporta como warning suave.
            return True, "csv_sniff_no_detecto_dialecto"
        return True, None
    except Exception as e:
        return False, f"error_lectura: {e}"


def _detect_encoding(path: Path) -> str:
    with open(path, "rb") as f:
        sample = f.read(65536)
    try:
        sample.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        sample.decode("cp1252")
        return "cp1252"
    except UnicodeDecodeError:
        return "latin-1"


def _estimate_tokens_whitespace(path: Path, encoding: str) -> int | None:
    try:
        with open(path, "r", encoding=encoding, errors="replace") as f:
            text = f.read()
        return len(text.split())
    except Exception:
        return None


def audit_corpus(corpus_path: Path, cfg: dict, errors_log: Path) -> dict:
    t0 = time.time()

    total_files = 0
    total_size = 0
    by_extension = Counter()
    by_formato = Counter()
    by_fenomeno = Counter()
    by_observatorio = Counter()
    by_carpeta = Counter()

    empty_files = []
    corrupted_files = []
    encoding_issues = []
    unknown_fenomeno_files = []
    hashes: dict[str, list[str]] = defaultdict(list)  # hash -> [rel_paths]

    per_extension_rows = []  # para CSV detallado

    for df in discover_corpus(corpus_path, cfg):
        total_files += 1
        total_size += df.size_bytes
        by_extension[df.extension or "(sin_extension)"] += 1
        by_formato[df.formato] += 1
        by_fenomeno[df.fenomeno] += 1
        by_observatorio[f"{df.fenomeno}/{df.observatorio}"] += 1
        carpeta = str(Path(df.rel_path).parent)
        by_carpeta[carpeta] += 1

        if df.fenomeno == "UNKNOWN" or df.observatorio == "UNKNOWN":
            unknown_fenomeno_files.append(df.rel_path)

        row = {
            "doc_id": df.doc_id,
            "rel_path": df.rel_path,
            "fenomeno": df.fenomeno,
            "observatorio": df.observatorio,
            "formato": df.formato,
            "extension": df.extension,
            "size_bytes": df.size_bytes,
            "is_empty": df.is_empty,
            "is_corrupted": False,
            "corrupt_reason": "",
            "encoding": "",
            "tokens_estimados": "",
            "hash": "",
        }

        if df.is_empty:
            empty_files.append(df.rel_path)
            append_jsonl(
                errors_log,
                {
                    "path": df.rel_path,
                    "error_type": "empty_file",
                    "message": "Archivo de tamaño 0 bytes",
                    "timestamp": time.time(),
                },
            )
            per_extension_rows.append(row)
            continue

        abs_path = Path(df.path)

        # --- Hash para deduplicación (streaming, ya definido en utils.io) ---
        try:
            h = file_hash(abs_path, cfg["audit"]["read_chunk_bytes"])
            row["hash"] = h
            hashes[h].append(df.rel_path)
        except Exception as e:
            row["hash"] = ""
            append_jsonl(
                errors_log,
                {
                    "path": df.rel_path,
                    "error_type": "hash_failed",
                    "message": str(e),
                    "timestamp": time.time(),
                },
            )

        # --- Validación por formato ---
        valid, reason = True, None
        if df.formato == "json":
            valid, reason = _check_json_valid(abs_path)
        elif df.formato == "pdf":
            valid, reason = _check_pdf_valid(abs_path)
        elif df.formato == "excel":
            valid, reason = _check_xlsx_valid(abs_path)
        elif df.formato == "imagen":
            valid, reason = _check_image_valid(abs_path)
        elif df.formato == "csv":
            enc = _detect_encoding(abs_path)
            row["encoding"] = enc
            valid, reason = _check_csv_valid(abs_path, enc)
        elif df.formato == "texto":
            row["encoding"] = _detect_encoding(abs_path)

        if not valid:
            row["is_corrupted"] = True
            row["corrupt_reason"] = reason or "desconocido"
            corrupted_files.append({"rel_path": df.rel_path, "reason": reason})
            append_jsonl(
                errors_log,
                {
                    "path": df.rel_path,
                    "error_type": "corrupted_or_invalid",
                    "message": reason or "desconocido",
                    "timestamp": time.time(),
                },
            )
        elif reason:  # válido pero con warning (p.ej. encoding no-utf8, sniff fallido)
            encoding_issues.append({"rel_path": df.rel_path, "note": reason})

        # --- Estimación de tokens (solo formatos de texto ligero, archivos no gigantes) ---
        if df.formato in ("texto", "csv", "json") and df.size_bytes <= LARGE_FILE_SKIP_TOKEN_ESTIMATE:
            enc = row["encoding"] or _detect_encoding(abs_path)
            row["encoding"] = enc
            n_tok = _estimate_tokens_whitespace(abs_path, enc)
            row["tokens_estimados"] = n_tok if n_tok is not None else "error"
        else:
            row["tokens_estimados"] = "pendiente_extraccion"

        per_extension_rows.append(row)

    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    n_duplicate_files = sum(len(v) - 1 for v in duplicates.values())  # extras, no el original

    elapsed = time.time() - t0

    summary = {
        "corpus_path": str(corpus_path),
        "total_files": total_files,
        "total_size_bytes": total_size,
        "total_size_gb": round(total_size / (1024 ** 3), 3),
        "by_extension": dict(by_extension),
        "by_formato": dict(by_formato),
        "by_fenomeno": dict(by_fenomeno),
        "by_observatorio": dict(by_observatorio),
        "n_carpetas": len(by_carpeta),
        "empty_files_count": len(empty_files),
        "empty_files": empty_files[:200],  # cap para no inflar el JSON
        "corrupted_files_count": len(corrupted_files),
        "corrupted_files": corrupted_files[:200],
        "encoding_issues_count": len(encoding_issues),
        "encoding_issues": encoding_issues[:200],
        "unknown_fenomeno_count": len(unknown_fenomeno_files),
        "unknown_fenomeno_files": unknown_fenomeno_files[:200],
        "duplicate_groups_count": len(duplicates),
        "duplicate_files_extra_count": n_duplicate_files,
        "duplicate_groups_sample": {k: v for i, (k, v) in enumerate(duplicates.items()) if i < 50},
        "elapsed_seconds": round(elapsed, 2),
    }

    return summary, per_extension_rows


def _sanity_check_vs_official(summary: dict, cfg: dict) -> list[str]:
    """Compara totales descubiertos vs el índice oficial agregado. Solo WARNINGS,
    nunca detiene el pipeline (el índice oficial es un agregado, no ground truth
    de nombres de archivo)."""
    warnings = []
    esperado_total = cfg.get("total_documentos_esperado")
    if esperado_total and summary["total_files"] != esperado_total:
        warnings.append(
            f"Total de archivos descubiertos ({summary['total_files']}) "
            f"difiere del total oficial esperado ({esperado_total})."
        )
    for fenomeno, observatorios in cfg.get("observatorios", {}).items():
        esperado_fenomeno = sum(o["total_esperado"] for o in observatorios)
        encontrado_fenomeno = summary["by_fenomeno"].get(fenomeno, 0)
        if encontrado_fenomeno != esperado_fenomeno:
            warnings.append(
                f"{fenomeno}: encontrados {encontrado_fenomeno}, "
                f"esperados {esperado_fenomeno} (según índice oficial)."
            )
    return warnings


def write_reports(summary: dict, rows: list[dict], warnings: list[str], reports_dir: Path) -> None:
    ensure_dir(reports_dir)

    # JSON completo
    with open(reports_dir / "corpus_audit.json", "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "warnings": warnings}, f, ensure_ascii=False, indent=2)

    # CSV detallado (una fila por archivo)
    csv_path = reports_dir / "corpus_audit.csv"
    fieldnames = [
        "doc_id", "rel_path", "fenomeno", "observatorio", "formato", "extension",
        "size_bytes", "is_empty", "is_corrupted", "corrupt_reason", "encoding",
        "tokens_estimados", "hash",
    ]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    # Resumen Markdown legible
    md_lines = [
        "# Auditoría del corpus — CODEFEST AD ASTRA 2026",
        "",
        f"- **Ruta auditada**: `{summary['corpus_path']}`",
        f"- **Total archivos**: {summary['total_files']}",
        f"- **Tamaño total**: {summary['total_size_gb']} GB",
        f"- **Carpetas distintas**: {summary['n_carpetas']}",
        f"- **Tiempo de auditoría**: {summary['elapsed_seconds']} s",
        "",
        "## Por formato",
        "",
        "| Formato | Archivos |",
        "|---|---|",
    ]
    for k, v in sorted(summary["by_formato"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {k} | {v} |")

    md_lines += ["", "## Por fenómeno", "", "| Fenómeno | Archivos |", "|---|---|"]
    for k, v in sorted(summary["by_fenomeno"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {k} | {v} |")

    md_lines += ["", "## Por observatorio", "", "| Fenómeno/Observatorio | Archivos |", "|---|---|"]
    for k, v in sorted(summary["by_observatorio"].items(), key=lambda x: -x[1]):
        md_lines.append(f"| {k} | {v} |")

    md_lines += [
        "",
        "## Problemas detectados",
        "",
        f"- Archivos vacíos: **{summary['empty_files_count']}**",
        f"- Archivos corruptos/inválidos: **{summary['corrupted_files_count']}**",
        f"- Archivos con problemas de encoding: **{summary['encoding_issues_count']}**",
        f"- Archivos sin fenómeno/observatorio identificado: **{summary['unknown_fenomeno_count']}**",
        f"- Grupos de duplicados (por hash): **{summary['duplicate_groups_count']}** "
        f"({summary['duplicate_files_extra_count']} archivos redundantes)",
        "",
    ]

    if warnings:
        md_lines += ["## ⚠️ Warnings vs índice oficial", ""]
        for w in warnings:
            md_lines.append(f"- {w}")
        md_lines.append("")

    md_lines += [
        "## Archivos generados",
        "",
        "- `reports/corpus_audit.json` — resumen completo + listas (capadas a 200 items)",
        "- `reports/corpus_audit.csv` — una fila por archivo, para inspección en Excel/pandas",
        "- `reports/errors.jsonl` — log de errores por archivo (vacíos, corruptos, hash fallido)",
        "",
    ]

    with open(reports_dir / "corpus_summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))


def sanity_check_vs_official(summary: dict, cfg: dict) -> list[str]:
    """Alias público de _sanity_check_vs_official (usado por el CLI y por tests)."""
    return _sanity_check_vs_official(summary, cfg)
