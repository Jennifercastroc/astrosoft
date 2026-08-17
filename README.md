# CODEFEST AD ASTRA 2026

Sistema de recuperación de información construido sobre el corpus oficial de
Codefest AD ASTRA 2026.

El sistema está orientado a resolver las 50 consultas oficiales del reto
mediante recuperación de información, búsqueda semántica y selección de
evidencia documental.

Las consultas están organizadas en tres fenómenos:

- F1 — IA y Capacidades Estratégicas
- F2 — Seguridad del Entorno Espacial
- F3 — Dinámicas Territoriales

## Estructura

```text
codefest_ad_astra/
├── config.yaml
├── data/
│   ├── raw/
│   ├── index/
│   ├── queries/
│   ├── processed/
│   └── chunks/
├── src/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── chunking/
│   ├── embeddings/
│   ├── retrieval/
│   ├── graph/
│   ├── evaluation/
│   └── utils/
├── scripts/
├── tests/
├── experiments/
├── artifacts/
├── entrega/
└── reports/
````

## Datos

El corpus original se mantiene fuera del repositorio debido a su tamaño.

Los documentos utilizados durante el desarrollo se almacenan localmente en
`data/raw/`.

La estructura esperada es:

```text
data/raw/
├── F1_IA_y_Capacidades_Estrategicas/
├── F2_Seguridad_Entorno_Espacial/
└── F3_Dinamicas_Territoriales/
```

El índice oficial de preguntas se encuentra en:

```text
data/index/Indice_Datos_Codefest_Indice.csv
data/queries/queries.jsonl
```

`queries.jsonl` contiene las 50 consultas oficiales utilizadas por el
pipeline.

## Pipeline

El procesamiento sigue las siguientes etapas:

```text
Corpus
  ↓
Descubrimiento y auditoría
  ↓
Extracción de texto
  ↓
Limpieza y normalización
  ↓
Chunking
  ↓
Embeddings
  ↓
Índice FAISS
  ↓
Recuperación
  ↓
Ranking / reranking
  ↓
Selección de evidencia
  ↓
Resultados
```

Cada documento conserva metadatos que permiten relacionar los fragmentos
recuperados con su documento de origen.

## Configuración

La configuración principal se encuentra en `config.yaml`.

En ella se definen las rutas del corpus, los modelos utilizados, los
parámetros de chunking, embeddings y recuperación.

El corpus puede especificarse directamente en el archivo de configuración o
mediante `--corpus-path` cuando el script lo soporte.

## Instalación

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Auditoría del corpus

La primera etapa permite revisar la estructura y el estado de los documentos
antes de iniciar el procesamiento.

```bash
python scripts/01_audit_corpus.py --corpus-path data/raw
```

La auditoría genera:

```text
reports/
├── corpus_audit.json
├── corpus_audit.csv
├── corpus_summary.md
└── errors.jsonl
```

Entre las verificaciones realizadas se encuentran archivos vacíos,
archivos corruptos, duplicados, formatos y clasificación de los documentos
dentro del corpus.

## Tests

Los tests utilizan un corpus pequeño incluido únicamente para validar el
funcionamiento del pipeline.

```bash
bash tests/build_fixture.sh
pytest tests/ -v
```

## Requisitos del reto

El sistema está diseñado alrededor de las restricciones establecidas para
Codefest AD ASTRA 2026.

En particular:

* El índice de recuperación utiliza FAISS.
* Los documentos y fragmentos mantienen una correspondencia estable con sus
  metadatos.
* El retrieval no utiliza modelos generativos.
* La recuperación puede combinar representaciones semánticas y métodos
  léxicos.
* Los fragmentos utilizados en los resultados corresponden al texto real del
  corpus.
* La entrega final debe contener 50 consultas con los documentos y
  fragmentos recuperados según el formato establecido por la competencia.

## Organización del desarrollo

| Etapa | Descripción                           |
| ----- | ------------------------------------- |
| 1     | Auditoría y descubrimiento del corpus |
| 2     | Extracción de documentos              |
| 3     | Limpieza y chunking                   |
| 4     | Embeddings e índice FAISS             |
| 5     | Baseline de recuperación              |
| 6     | BM25 y fusión de resultados           |
| 7     | Reranking                             |
| 8     | Ranking documental                    |
| 9     | Grafo de conocimiento                 |
| 10    | Generación de resultados              |
| 11    | Validación de la entrega              |
| 12    | Informe técnico                       |
