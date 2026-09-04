#!/usr/bin/env python3
"""
scripts/03_clean.py
Phase 3a: Clean and normalize extracted text from documents_extracted.jsonl
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.io import load_config, read_jsonl, resolve_path, write_jsonl
from src.utils.logging import get_logger

log = get_logger("clean")


def clean_text(text: str) -> str:
    if not text:
        return ""
    # Replace non-breaking spaces and control characters (except newlines)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Collapse multiple blank lines to a maximum of two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse consecutive horizontal spaces
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def main():
    cfg = load_config()
    processed_dir = resolve_path(cfg["paths"]["processed_dir"])
    input_file = processed_dir / "documents_extracted.jsonl"
    output_file = processed_dir / "documents_cleaned.jsonl"

    if not input_file.exists():
        log.error(f"Input file not found: {input_file}. Run 02_extract.py first.")
        sys.exit(1)

    log.info(f"Cleaning extracted documents from: {input_file}")
    cleaned_records = []

    for record in read_jsonl(input_file):
        cleaned_str = clean_text(record.get("text", ""))
        if cleaned_str:
            record["text"] = cleaned_str
            record["word_count"] = len(cleaned_str.split())
            cleaned_records.append(record)

    write_jsonl(output_file, cleaned_records)
    log.info(f"Cleaning complete! Saved {len(cleaned_records)} documents to: {output_file}")


if __name__ == "__main__":
    main()