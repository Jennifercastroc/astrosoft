#!/usr/bin/env python3
"""
scripts/00_build_queries.py

Construye data/queries/queries.jsonl a partir de las 50 consultas oficiales
(texto provisto textualmente por el usuario / Extracto_Preguntas_50_v2.pdf).

El campo `fenomeno_hint` es una HEURÍSTICA interna basada en el rango de ID
(q001-q016 ~ F1, q017-q032 ~ F2, q033-q050 ~ F3), consistente con los conteos
de observatorios por fenómeno del índice oficial (16/16/18). NO es una
etiqueta oficial: se usa únicamente para evaluación interna estratificada
(proxy), nunca para filtrar el corpus durante el retrieval real -- las 50
consultas se deben responder contra el corpus completo.

Uso:
    python scripts/00_build_queries.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.io import resolve_path, write_jsonl, load_config  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402

log = get_logger("build_queries")

# Texto oficial, transcrito verbatim de Extracto_Preguntas_50_v2.pdf / prompt del usuario.
QUERIES_RAW = [
    "¿Cómo está transformando la inteligencia artificial la capacidad de los Estados para prevenir, detectar y contrarrestar amenazas NBQR?",
    "¿Cómo están empleando los sistemas no tripulados potenciados por IA para aumentar la efectividad de las operaciones militares?",
    "¿Qué lecciones dejan los conflictos recientes sobre el empleo de inteligencia artificial en operaciones militares?",
    "¿Qué riesgos representa la escasez de talento especializado en inteligencia artificial para el desarrollo de capacidades de defensa?",
    "¿Qué implicaciones estratégicas tiene la dependencia de tecnologías extranjeras de IA para la autonomía y la seguridad nacional de Colombia?",
    "¿Qué riesgos operacionales y jurídicos implica incorporar inteligencia artificial en inteligencia militar sin una doctrina, políticas y protocolos consolidados?",
    "¿Qué desafíos plantea el empleo de sistemas autónomos o semiautónomos frente al Derecho Internacional Humanitario y la atribución de responsabilidades?",
    "¿Cómo están empleando las fuerzas militares el análisis de inteligencia asistido por IA, el targeting inteligente y los enjambres de drones, y qué oportunidades representan para países con geografías complejas como Colombia?",
    "¿Cómo está redefiniendo la inteligencia artificial las tácticas y conceptos de operación en los conflictos armados contemporáneos?",
    "¿Qué capacidades basadas en IA fortalecen la detección, identificación y neutralización de drones utilizados por actores armados?",
    "¿Cuáles son las principales barreras para incorporar inteligencia artificial en los procesos operacionales y de inteligencia de las Fuerzas Militares?",
    "¿Cómo puede la experiencia operacional acumulada por las Fuerzas Militares convertirse en conocimiento útil para entrenar sistemas de inteligencia artificial?",
    "¿Cuáles son las principales amenazas cibernéticas que afectan el despliegue seguro de sistemas de inteligencia artificial en infraestructuras críticas?",
    "¿Cómo limita la disponibilidad de infraestructura de cómputo avanzado el desarrollo de capacidades nacionales de inteligencia artificial para defensa?",
    "¿Qué riesgos estratégicos genera la dependencia de semiconductores y hardware especializado para el desarrollo de capacidades militares basadas en IA?",
    "¿Qué ventajas estratégicas obtienen los actores que incorporan inteligencia artificial y drones de bajo costo, y cuáles son los riesgos de retrasar la transformación tecnológica en defensa?",
    "¿Qué restricciones impone el Derecho Internacional en el Espacio en la regulación del uso de armas?",
    "¿Qué capacidades contraespaciales representan actualmente la mayor amenaza para los sistemas satelitales?",
    "¿Cómo se está empleando la guerra electrónica para interferir sistemas espaciales y qué incidentes recientes lo evidencian?",
    "¿Qué incidentes recientes de spoofing han comprometido servicios satelitales y qué vulnerabilidades revelan?",
    "¿Qué implicaciones militares tienen las maniobras de proximidad y encuentro (RPO) realizadas por satélites?",
    "¿Qué evidencias existen sobre el desarrollo de armas de energía dirigida con potencial empleo contra activos espaciales?",
    "¿Cuáles son las principales vulnerabilidades cibernéticas de la infraestructura satelital?",
    "¿Qué países están desarrollando capacidades láser con potencial empleo contra sistemas espaciales?",
    "¿Qué implicaciones tendría el despliegue de una capacidad nuclear antisatélite en órbita?",
    "¿Cuál ha sido el impacto de las pruebas antisatélite sobre la generación de desechos orbitales?",
    "¿Qué desafíos plantea el uso de inteligencia artificial en las operaciones espaciales?",
    "¿Qué capacidades estratégicas ha demostrado China mediante operaciones de servicio y reabastecimiento en órbita?",
    "¿Qué capacidades operacionales evidencian las maniobras realizadas recientemente por satélites rusos en órbita GEO?",
    "¿Cómo han evolucionado las operaciones espaciales dinámicas dentro de la estrategia espacial estadounidense?",
    "¿Qué cambios doctrinales han fortalecido el empleo militar de las capacidades espaciales de Corea del Norte?",
    "¿Qué lecciones ha dejado el conflicto entre Rusia y Ucrania sobre el empleo militar del dominio espacial?",
    "¿Cómo utilizan los grupos armados ilegales el control territorial para sustituir funciones del Estado y consolidar su influencia sobre las comunidades?",
    "¿Qué corredores geográficos y territorios estratégicos son priorizados por los grupos armados para fortalecer su control operacional?",
    "¿Cómo contribuyen las economías ilícitas al deterioro ambiental y al fortalecimiento de los grupos armados en América Latina?",
    "¿Qué actividades económicas ilegales convergen con la explotación de recursos naturales en zonas de conflicto?",
    "¿De qué manera el crimen organizado logra fortalecer su capacidad de influencia sobre las instituciones del Estado?",
    "¿Qué innovaciones tácticas recientes han incorporado los grupos armados para aumentar su capacidad operacional?",
    "¿Qué capacidades han fortalecido los grupos armados para consolidar y expandir su control territorial?",
    "¿Cómo utilizan los grupos armados ilegales la imposición de normas de conducta para ejercer control social sobre la población civil en regiones con baja presencia del Estado?",
    "¿Qué corredores de movilidad y territorios estratégicos son priorizados por los Grupos Armados Organizados (GAO), Grupos Armados Organizados Residuales (GAOR) y Grupos Delictivos Organizados (GDO) para asegurar sus economías ilícitas y fortalecer su control territorial?",
    "¿De qué manera la minería ilegal de oro financia el fortalecimiento y la expansión territorial de los Grupos Armados Organizados (GAO), Grupos Armados Organizados Residuales (GAOR) y Grupos Delictivos Organizados (GDO) en departamentos como Chocó, Antioquia y Bolívar?",
    "¿De qué manera el narcotráfico financia el fortalecimiento y la expansión territorial de los Grupos Armados Organizados (GAO), Grupos Armados Organizados Residuales (GAOR) y Grupos Delictivos Organizados (GDO) en departamentos como Norte de Santander, Arauca, Córdoba y el Cauca?",
    "¿Qué factores incrementan el riesgo de reclutamiento, uso y utilización de niños, niñas y adolescentes en zonas de disputa entre grupos armados organizados?",
    "¿Cómo afectan las disputas entre grupos criminales la seguridad de la población civil y el incremento de los homicidios selectivos?",
    "¿Qué minerales estratégicos están siendo utilizados por los grupos armados organizados en Colombia y la región para financiar el conflicto?",
    "¿Cómo la disputa por el control de rutas aéreas incrementa el tráfico de narcóticos, armas y mercancías de contrabando?",
    "¿Cómo influyen las dinámicas de exploración y explotación petrolera en la inserción y fortalecimiento de grupos armados que buscan controlar rentas derivadas de recursos estratégicos?",
    "¿De qué manera el accionar de grupos armados interfiere y obstaculiza el desarrollo de los procesos de restitución de tierras?",
    "¿Cómo adaptan las organizaciones criminales sus estrategias de control territorial frente a las transformaciones políticas, ambientales, tecnológicas y económicas en América Latina?",
]

assert len(QUERIES_RAW) == 50, f"Se esperaban 50 consultas, hay {len(QUERIES_RAW)}"


def _fenomeno_hint(idx_1based: int) -> str:
    """Heurística por rango de ID, consistente con conteos oficiales (16/16/18).
    Ver docstring del módulo: NO es etiqueta oficial."""
    if 1 <= idx_1based <= 16:
        return "F1"
    if 17 <= idx_1based <= 32:
        return "F2"
    return "F3"


def build_queries() -> list[dict]:
    records = []
    for i, text in enumerate(QUERIES_RAW, start=1):
        records.append({
            "query_id": f"q{i:03d}",
            "text": text,
            "fenomeno_hint": _fenomeno_hint(i),
            "idioma": "es",
        })
    return records


def main():
    cfg = load_config()
    out_path = resolve_path(cfg["paths"]["queries_path"])
    records = build_queries()
    n = write_jsonl(out_path, records)
    log.info(f"Escritas {n} consultas en {out_path}")
    assert n == 50


if __name__ == "__main__":
    main()
