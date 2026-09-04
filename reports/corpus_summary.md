# Auditoría del corpus — CODEFEST AD ASTRA 2026

- **Ruta auditada**: `C:\Users\jennc\OneDrive\Escritorio\astronomía\astrosoft\data\raw`
- **Total archivos**: 1831
- **Tamaño total**: 2.892 GB
- **Carpetas distintas**: 140
- **Tiempo de auditoría**: 95.94 s

## Por formato

| Formato | Archivos |
|---|---|
| json | 964 |
| pdf | 753 |
| pbf | 73 |
| csv | 26 |
| imagen | 8 |
| excel | 5 |
| texto | 1 |
| otro | 1 |

## Por fenómeno

| Fenómeno | Archivos |
|---|---|
| F3 | 899 |
| F2 | 473 |
| F1 | 459 |

## Por observatorio

| Fenómeno/Observatorio | Archivos |
|---|---|
| F3/ALERTAS | 425 |
| F2/CSIS | 214 |
| F1/ATLCOUNCIL | 186 |
| F3/SIPRI | 130 |
| F2/SWF | 129 |
| F1/CSET | 127 |
| F3/RESDAL | 109 |
| F3/CEEEP | 82 |
| F3/AMAZONUW | 75 |
| F1/AIINDEX | 65 |
| F2/INPE | 59 |
| F2/ESA | 40 |
| F3/CEOBS | 40 |
| F3/MAPPOEA | 37 |
| F1/DAIO | 35 |
| F2/UNOOSA | 31 |
| F1/CENIA | 27 |
| F1/ILIA | 10 |
| F1/RUTAN | 7 |
| F1/DEFENSA21 | 2 |
| F3/UNKNOWN | 1 |

## Problemas detectados

- Archivos vacíos: **0**
- Archivos corruptos/inválidos: **2**
- Archivos con problemas de encoding: **0**
- Archivos sin fenómeno/observatorio identificado: **1**
- Grupos de duplicados (por hash): **0** (0 archivos redundantes)

## ⚠️ Warnings vs índice oficial

- Total de archivos descubiertos (1831) difiere del total oficial esperado (1826).
- F2: encontrados 473, esperados 479 (según índice oficial).
- F3: encontrados 899, esperados 888 (según índice oficial).

## Archivos generados

- `reports/corpus_audit.json` — resumen completo + listas (capadas a 200 items)
- `reports/corpus_audit.csv` — una fila por archivo, para inspección en Excel/pandas
- `reports/errors.jsonl` — log de errores por archivo (vacíos, corruptos, hash fallido)
