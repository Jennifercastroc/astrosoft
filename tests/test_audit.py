"""
Tests unitarios para el pipeline de auditoría (Fase 1).
Usa el fixture pequeño en tests/fixtures/mini_corpus (generado por build_fixture.sh).

Ejecutar:
    bash tests/build_fixture.sh   # solo la primera vez / si se borró el fixture
    pytest tests/test_audit.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from src.ingestion.discover import discover_corpus  # noqa: E402
from src.utils.io import load_config, stable_id  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mini_corpus"


@pytest.fixture(scope="module")
def cfg():
    return load_config()


def test_fixture_exists():
    assert FIXTURE_DIR.exists(), "Corre `bash tests/build_fixture.sh` antes de los tests"


def test_discover_finds_all_files(cfg):
    files = list(discover_corpus(FIXTURE_DIR, cfg))
    assert len(files) == 10


def test_discover_infers_known_observatorios(cfg):
    files = {f.rel_path: f for f in discover_corpus(FIXTURE_DIR, cfg)}
    reporte = files["F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/reporte1.pdf"]
    assert reporte.fenomeno == "F1"
    assert reporte.observatorio == "AIINDEX"


def test_discover_marks_unknown_when_not_recognized(cfg):
    files = {f.rel_path: f for f in discover_corpus(FIXTURE_DIR, cfg)}
    huerfano = files["carpeta_sin_fenomeno_reconocible/huerfano.txt"]
    assert huerfano.fenomeno == "UNKNOWN"
    assert huerfano.observatorio == "UNKNOWN"


def test_discover_flags_empty_files(cfg):
    files = {f.rel_path: f for f in discover_corpus(FIXTURE_DIR, cfg)}
    vacio = files["F1_IA_y_Capacidades_Estrategicas/RutaN_GEIAL/vacio.txt"]
    assert vacio.is_empty is True
    assert vacio.size_bytes == 0


def test_doc_id_is_stable_and_reproducible(cfg):
    files1 = {f.rel_path: f.doc_id for f in discover_corpus(FIXTURE_DIR, cfg)}
    files2 = {f.rel_path: f.doc_id for f in discover_corpus(FIXTURE_DIR, cfg)}
    assert files1 == files2, "doc_id debe ser determinístico entre corridas"


def test_stable_id_deterministic():
    assert stable_id("a", "b") == stable_id("a", "b")
    assert stable_id("a", "b") != stable_id("a", "c")


def test_audit_end_to_end(tmp_path, cfg):
    """Corre audit_corpus() completo sobre el fixture y valida resultados clave."""
    from scripts.audit_lib import audit_corpus

    errors_log = tmp_path / "errors.jsonl"
    summary, rows = audit_corpus(FIXTURE_DIR, cfg, errors_log)

    assert summary["total_files"] == 10
    assert summary["empty_files_count"] == 1
    assert summary["corrupted_files_count"] == 2  # dato_corrupto.json + foto_rota.jpg
    assert summary["duplicate_groups_count"] == 1
    assert summary["duplicate_files_extra_count"] == 1
    assert summary["unknown_fenomeno_count"] == 1
    assert errors_log.exists()
