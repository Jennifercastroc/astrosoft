#!/usr/bin/env python3
"""
scripts/04_chunk.py
Phase 3b: Sentence-aware chunking over cleaned documents into data/chunks/chunks.jsonl
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.io import ensure_dir, load_config, read_jsonl, resolve_path, stable_id, write_jsonl
from src.utils.logging import get_logger

log = get_logger("chunk")


def split_into_sentences(text: str) -> list[str]:
    """Splits text on sentence boundaries without breaking mid-sentence."""
    sentence_endings = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9¿¡])")
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def create_chunks(doc: dict, max_words: int = 220) -> list[dict]:
    text = doc.get("text", "")
    sentences = split_into_sentences(text)
    
    chunks = []
    current_sentences = []
    current_word_count = 0
    chunk_index = 0

    for sent in sentences:
        sent_words = len(sent.split())
        
        # If single sentence exceeds max_words, force keep it intact to avoid cutting sentences
        if current_word_count + sent_words > max_words and current_sentences:
            chunk_text = " ".join(current_sentences)
            chunk_id = f"{doc['doc_id']}_c{chunk_index:04d}"
            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc["doc_id"],
                "rel_path": doc["rel_path"],
                "fenomeno": doc["fenomeno"],
                "observatorio": doc["observatorio"],
                "chunk_index": chunk_index,
                "text": chunk_text,
                "word_count": len(chunk_text.split()),
            })
            chunk_index += 1
            current_sentences = [sent]
            current_word_count = sent_words
        else:
            current_sentences.append(sent)
            current_word_count += sent_words

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunk_id = f"{doc['doc_id']}_c{chunk_index:04d}"
        chunks.append({
            "chunk_id": chunk_id,
            "doc_id": doc["doc_id"],
            "rel_path": doc["rel_path"],
            "fenomeno": doc["fenomeno"],
            "observatorio": doc["observatorio"],
            "chunk_index": chunk_index,
            "text": chunk_text,
            "word_count": len(chunk_text.split()),
        })

    return chunks


def main():
    cfg = load_config()
    processed_dir = resolve_path(cfg["paths"]["processed_dir"])
    chunks_dir = resolve_path(cfg["paths"]["chunks_dir"])
    
    input_file = processed_dir / "documents_cleaned.jsonl"
    output_file = chunks_dir / "chunks.jsonl"
    ensure_dir(chunks_dir)

    if not input_file.exists():
        log.error(f"Input file not found: {input_file}. Run 03_clean.py first.")
        sys.exit(1)

    log.info(f"Chunking cleaned documents from: {input_file}")
    all_chunks = []

    for doc in read_jsonl(input_file):
        doc_chunks = create_chunks(doc, max_words=220)
        all_chunks.extend(doc_chunks)

    write_jsonl(output_file, all_chunks)
    log.info(f"Chunking complete! Generated {len(all_chunks)} chunks saved to: {output_file}")


if __name__ == "__main__":
    main()