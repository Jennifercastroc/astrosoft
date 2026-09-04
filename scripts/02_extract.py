#!/usr/bin/env python3
"""
scripts/02_extract.py
Phase 2: Extract text from heterogeneous formats into data/processed/documents_extracted.jsonl
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pymupdf  # PyMuPDF
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.discover import discover_corpus
from src.utils.io import append_jsonl, ensure_dir, load_config, resolve_path, write_jsonl
from src.utils.logging import get_logger

log = get_logger("extract")


def extract_pdf(path: Path) -> str:
    text_parts = []
    with pymupdf.open(path) as doc:
        for page in doc:
            text = page.get_text("text")
            if text:
                text_parts.append(text.strip())
    return "\n\n".join(text_parts)


def extract_json(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return "\n".join(str(v) for k, v in data.items() if isinstance(v, (str, int, float)))
    elif isinstance(data, list):
        return "\n".join(str(item) for item in data if isinstance(item, (str, dict)))
    return str(data)


def extract_tabular(path: Path, formato: str) -> str:
    df = pd.read_csv(path) if formato == "csv" else pd.read_excel(path)
    return df.to_string(index=False)


def extract_txt(path: Path) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    cfg = load_config()
    corpus_path = resolve_path(cfg["paths"]["corpus_path"])
    processed_dir = resolve_path(cfg["paths"]["processed_dir"])
    errors_log = resolve_path(cfg["paths"]["errors_log"])

    ensure_dir(processed_dir)
    records = []
    success_count = 0
    error_count = 0

    log.info(f"Extracting corpus from: {corpus_path}")

    for df in discover_corpus(corpus_path, cfg):
        if df.is_empty:
            continue

        abs_path = Path(df.path)
        extracted_text = ""
        status = "success"
        error_msg = ""

        try:
            if df.formato == "pdf":
                extracted_text = extract_pdf(abs_path)
            elif df.formato == "json":
                extracted_text = extract_json(abs_path)
            elif df.formato in ("csv", "excel"):
                extracted_text = extract_tabular(abs_path, df.formato)
            elif df.formato == "texto":
                extracted_text = extract_txt(abs_path)
            elif df.formato in ("pbf", "imagen"):
                status = "skipped"
                error_msg = f"Format '{df.formato}' is non-textual / skipped"
            else:
                status = "skipped"
                error_msg = f"Unsupported format: {df.formato}"

        except Exception as e:
            status = "error"
            error_msg = str(e)

        if status == "success" and extracted_text.strip():
            records.append({
                "doc_id": df.doc_id,
                "rel_path": df.rel_path,
                "fenomeno": df.fenomeno,
                "observatorio": df.observatorio,
                "formato": df.formato,
                "text": extracted_text,
                "word_count": len(extracted_text.split()),
            })
            success_count += 1
        else:
            error_count += 1
            append_jsonl(errors_log, {
                "doc_id": df.doc_id,
                "path": df.rel_path,
                "error_type": "extraction_" + status,
                "message": error_msg or "Extracted text was empty",
                "timestamp": time.time(),
            })

    out_path = processed_dir / "documents_extracted.jsonl"
    write_jsonl(out_path, records)
    log.info(f"Extraction complete! Extracted: {success_count} | Skipped/Errors: {error_count}")
    log.info(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()