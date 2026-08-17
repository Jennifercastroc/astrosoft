#!/usr/bin/env python3
"""
scripts/01_audit_corpus.py

CLI de la auditoría del corpus (Fase 1 / Prioridad 1). La lógica vive en
scripts/audit_lib.py (así es testeable con pytest sin pasar por argparse).

Genera:
  reports/corpus_audit.json
  reports/corpus_audit.csv
  reports/corpus_summary.md
  reports/errors.jsonl

Uso:
    python scripts/01_audit_corpus.py
    python scripts/01_audit_corpus.py --corpus-path /ruta/alternativa
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite ejecutar como `python scripts/01_audit_corpus.py` desde cualquier cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit_lib import audit_corpus, sanity_check_vs_official, write_reports  # noqa: E402
from src.utils.io import PROJECT_ROOT, ensure_dir, load_config, resolve_path  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402

log = get_logger("audit_corpus_cli")


def main():
    parser = argparse.ArgumentParser(description="Auditoría incremental del corpus.")
    parser.add_argument("--corpus-path", default=None, help="Override de paths.corpus_path")
    parser.add_argument("--config", default=None, help="Ruta a config.yaml (default: raíz del proyecto)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    corpus_path = resolve_path(args.corpus_path or cfg["paths"]["corpus_path"])
    errors_log = resolve_path(cfg["paths"]["errors_log"])
    reports_dir = resolve_path(cfg["paths"]["reports_dir"])

    log.info(f"PROJECT_ROOT = {PROJECT_ROOT}")
    log.info(f"Auditando corpus en: {corpus_path}")

    if not corpus_path.exists():
        log.error(
            f"corpus_path no existe: {corpus_path}\n"
            "-> Ajusta 'paths.corpus_path' en config.yaml o usa --corpus-path, "
            "y asegúrate de que el corpus esté descargado/montado localmente."
        )
        sys.exit(1)

    # Reinicia errors.jsonl en cada corrida para no acumular corridas viejas.
    ensure_dir(errors_log.parent)
    if errors_log.exists():
        errors_log.unlink()

    summary, rows = audit_corpus(corpus_path, cfg, errors_log)
    warnings = sanity_check_vs_official(summary, cfg)
    write_reports(summary, rows, warnings, reports_dir)

    log.info(f"Total archivos: {summary['total_files']}")
    log.info(
        f"Vacíos: {summary['empty_files_count']} | Corruptos: {summary['corrupted_files_count']} | "
        f"Duplicados (extra): {summary['duplicate_files_extra_count']}"
    )
    if warnings:
        for w in warnings:
            log.warning(w)
    log.info(f"Reportes escritos en: {reports_dir}")
    log.info("Listo. Revisa reports/corpus_summary.md")


if __name__ == "__main__":
    main()
