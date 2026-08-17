#!/bin/bash
set -e
cd "$(dirname "$0")/.."

BASE="tests/fixtures/mini_corpus"
rm -rf "$BASE"
mkdir -p "$BASE/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford"
mkdir -p "$BASE/F1_IA_y_Capacidades_Estrategicas/RutaN_GEIAL"
mkdir -p "$BASE/F2_Seguridad_del_Entorno_Espacial/SWF_Counterspace"
mkdir -p "$BASE/F3_Dinamicas_Territoriales/Amazon_Underworld"
mkdir -p "$BASE/carpeta_sin_fenomeno_reconocible"

printf '%%PDF-1.4\n%%%%EOF' > "$BASE/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/reporte1.pdf"

cat > "$BASE/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/dato1.json" << 'EOF'
{"title": "AI Index Report", "body": "Contenido de prueba sobre inteligencia artificial.", "source": "https://example.com/x"}
EOF

cat > "$BASE/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/dato_corrupto.json" << 'EOF'
{"title": "roto", "body": "falta cerrar llave"
EOF

touch "$BASE/F1_IA_y_Capacidades_Estrategicas/RutaN_GEIAL/vacio.txt"

echo "Este es un texto de prueba en espanol con varias palabras para estimar tokens." > "$BASE/F1_IA_y_Capacidades_Estrategicas/RutaN_GEIAL/nota.txt"

cat > "$BASE/F2_Seguridad_del_Entorno_Espacial/SWF_Counterspace/datos.csv" << 'EOF'
id,nombre,valor
1,alpha,10
2,beta,20
EOF

cp "$BASE/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/dato1.json" \
   "$BASE/F2_Seguridad_del_Entorno_Espacial/SWF_Counterspace/dato1_copia.json"

echo "esto no es una imagen real" > "$BASE/F2_Seguridad_del_Entorno_Espacial/SWF_Counterspace/foto_rota.jpg"

echo "contenido huerfano" > "$BASE/carpeta_sin_fenomeno_reconocible/huerfano.txt"

cat > "$BASE/F3_Dinamicas_Territoriales/Amazon_Underworld/reporte.json" << 'EOF'
{"title": "Reporte territorial", "body": "Analisis de dinamicas territoriales en la region."}
EOF

find "$BASE" -type f | sort
