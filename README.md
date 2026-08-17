# CODEFEST AD ASTRA 2026 — Etapa 1: Base de Conocimiento

Sistema de recuperación de conocimiento (retrieval) sobre el corpus de ADL,
para las 50 consultas oficiales (q001–q050) distribuidas en tres fenómenos:

- **F1** — IA y Capacidades Estratégicas
- **F2** — Seguridad del Entorno Espacial
- **F3** — Dinámicas Territoriales

> **Estado actual: FASE 1 (auditoría) — lista para correr.**
> Este README se completa incrementalmente a medida que avanzan las fases.
> Ver `PROGRESS.md` para el detalle fase por fase.

## 1. Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Estructura del proyecto

```
codefest_ad_astra/
├── config.yaml              # TODA la configuración (rutas, encoder, chunking, retrieval...)
├── data/
│   ├── raw/                 # <-- AQUÍ va el corpus real (no versionado, ver abajo)
│   ├── index/               # Índice oficial (CSV agregado por observatorio)
│   ├── queries/              # queries.jsonl (50 consultas oficiales)
│   ├── processed/            # Texto extraído por documento (Fase 2)
│   └── chunks/                # Chunks generados (Fase 3)
├── artifacts/                 # FAISS + metadata + grafo (generados)
├── entrega/                   # Entregable final (resultados.jsonl, generador.py, base_vectorial/)
├── src/                        # Código de librería (importable)
│   ├── ingestion/              # Descubrimiento + loaders por formato
│   ├── preprocessing/          # Limpieza, idioma, metadata
│   ├── chunking/                 # Estrategias de chunking
│   ├── embeddings/               # Encoders
│   ├── retrieval/                # FAISS, BM25, fusión, reranking, ranking documental
│   ├── graph/                    # Grafo de conocimiento (opcional)
│   ├── evaluation/               # Validación + evaluación interna (proxy)
│   └── utils/                    # io, logging, validation
├── scripts/                     # CLIs numerados, uno por fase del pipeline
├── tests/                       # Tests unitarios + fixtures sintéticos pequeños
├── experiments/                  # results.csv + configs de cada experimento
└── reports/                      # Salida de la auditoría (generado, no versionado)
```

## 3. ⚠️ Cómo apuntar al corpus real (IMPORTANTE)

El corpus (~1.826 documentos, varios GB) **no está incluido en este repo**
(ver `.gitignore`). Antes de correr cualquier script:

1. Descarga/monta el corpus localmente.
2. Edita `config.yaml` → `paths.corpus_path` apuntando a esa carpeta, **o**
   pasa `--corpus-path /ruta/al/corpus` a los scripts que lo soportan.

El descubrimiento de la estructura de carpetas es **automático**
(`src/ingestion/discover.py`): no asume nombres de carpeta fijos más allá de
intentar reconocer los observatorios oficiales (ver `config.yaml` →
`observatorios`); lo que no reconoce lo marca como `UNKNOWN` en vez de
descartarlo o inventar una clasificación.

## 4. Índice oficial y consultas (ya incluidos)

- `data/index/Indice_Datos_Codefest_Indice.csv` — índice agregado oficial
  (encoding `cp1252`, no UTF-8 — ver también la copia normalizada
  `Indice_Datos_Codefest_Indice_utf8.csv`). Es un **resumen por observatorio**,
  no un manifiesto por archivo; se usa solo como sanity-check de totales
  durante la auditoría.
- `data/queries/queries.jsonl` — las 50 consultas oficiales, generadas con:
  ```bash
  python scripts/00_build_queries.py
  ```

## 5. Auditoría del corpus (Fase 1 — lista para correr)

```bash
python scripts/01_audit_corpus.py
# o, si prefieres no editar config.yaml:
python scripts/01_audit_corpus.py --corpus-path /ruta/al/corpus
```

Genera:
- `reports/corpus_audit.json` — resumen completo + listas de problemas
- `reports/corpus_audit.csv` — una fila por archivo descubierto
- `reports/corpus_summary.md` — resumen legible (tablas por formato/fenómeno/observatorio)
- `reports/errors.jsonl` — log de archivos vacíos/corruptos/con error

**Comparación automática contra el índice oficial**: el script compara los
totales descubiertos contra los totales esperados por fenómeno
(`config.yaml` → `observatorios`) y emite **warnings** (nunca falla el
pipeline) si hay discrepancias — útil para detectar carpetas mal nombradas
o observatorios faltantes.

Este script **te lo debes ejecutar tú** (o compartirme el corpus / darme
acceso vía un conector soportado) porque el corpus vive fuera de mi entorno
de ejecución. Pégame el contenido de `reports/corpus_summary.md` (o el
archivo completo) y sigo iterando con datos reales.

## 6. Tests

```bash
bash tests/build_fixture.sh   # genera un mini-corpus sintético (solo para tests)
pytest tests/ -v
```

Los tests **no** requieren el corpus real: usan un fixture pequeño y
determinístico en `tests/fixtures/mini_corpus/` para validar que el
descubrimiento, la detección de duplicados/corruptos/vacíos y la generación
de reportes funcionan correctamente.

## 7. Próximos pasos (pendientes, no implementados aún)

| Fase | Script | Estado |
|---|---|---|
| 0 — Inspección | — | ✅ hecho |
| 1 — Auditoría | `01_audit_corpus.py` | ✅ código listo, **pendiente correr sobre corpus real** |
| 2 — Extracción | `02_extract.py` | ⏳ pendiente |
| 3 — Chunking | `03_clean.py` / `04_chunk.py` | ⏳ pendiente |
| 4 — Embeddings + FAISS | `05_embed.py` / `06_build_index.py` | ⏳ pendiente |
| 5 — Baseline retrieval | — | ⏳ pendiente |
| 6 — BM25 + RRF | `07_build_bm25.py` | ⏳ pendiente |
| 7 — Reranking | — | ⏳ pendiente |
| 8 — Ranking documental | — | ⏳ pendiente |
| 9 — Grafo (opcional) | `09_build_graph.py` | ⏳ pendiente, solo si sobra tiempo |
| 10 — Generador | `10_generate_results.py` / `entrega/generador.py` | ⏳ pendiente |
| 11 — Validación | `11_validate_submission.py` | ⏳ pendiente |
| 12 — Informe técnico | — | ⏳ pendiente |

## 8. Reglas duras del reto (recordatorio, ver informe técnico para más detalle)

- FAISS obligatorio, índice persistente, `metadata.jsonl` con correspondencia
  estable al ID interno del índice.
- **Prohibido** usar modelos generativos/decoder (GPT, Claude, Gemini, LLaMA...)
  en cualquier parte del retrieval (reranking, expansión de query, filtrado,
  síntesis). Solo embeddings, FAISS, BM25, cross-encoders no generativos,
  reglas determinísticas.
- Ningún chunk puede cortar una oración.
- `resultados.jsonl`: exactamente 50 líneas, 3 documentos y 10 fragmentos
  por consulta, fragmentos ≤ 250 palabras, texto real (no generado).
- Licencias de cualquier modelo usado en el grafo (NER/RE): **solo**
  Apache-2.0 / MIT / CC-BY-4.0. `CC BY-NC-SA 4.0` está prohibida (confirmado
  por organizadores en `Q_A_codefest.xlsx`).
