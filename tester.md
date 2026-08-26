# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 24/08/2026

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — no completar hasta cerrar todo el testing)* |
| Reason for recommendation | *(pendiente)* |

## Testing Overview

*(borrador, ampliar al final)*

- Tester: Cristian Páez (equipo Argentina).
- Documentación completa revisada antes de tocar código.
- Bloqueante de acceso al repositorio de código: sin acceso del 12/08 al 19/08 (una semana completa de la fase de testing).
- Entorno técnico R instalado y verificado en notebook sin permisos de administrador (R 4.4.0, Java 21 vía rJavaEnv, Quarto 1.9.38 portable).
- Pipeline R corrido end-to-end con datos reales, usando Malawi como caso de control (mismo país usado por el Developer como prototipo). Dashboard R confirmado visualmente.
- Entorno técnico Python resuelto vía Miniconda (modo "Just Me", sin admin), tras encontrar que un paquete (`cykhash`) requiere binarios que solo conda-forge distribuye para Windows.
- `data_preparation.py` (Python) corrido end-to-end con éxito, mismo caso Malawi, mismo dataset de facilities que R (para comparación consistente).
- Pendiente: `pop_travel_times.py` y dashboard Python, y correr con Argentina (caso pedido explícitamente por el Developer).

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| El pipeline no crea automáticamente las carpetas de salida (`data/boundaries/`, `data/poi/`, `data/population/`, etc.). Si no existen previamente, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o dar un mensaje claro de qué falta. | Minor |
| La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real descargado de HDX trae `X`, `Y` en mayúscula. No rompió el pipeline, pero la documentación no coincide exactamente con el dato real descargado. | Minor |
| La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/error 500 en nuestra prueba. Se resolvió usando un archivo local de geoBoundaries como fallback (camino ya contemplado por la guía), pero vale la pena que el Developer sepa que la vía automática puede no ser confiable y ofrecer el fallback más explícitamente en la documentación. | Minor |
| El campo `ownership` aparece como `NA` en el popup del dashboard para varias facilities. No es un bug del código — el dato no viene completo en la fuente healthsites.io usada para esta prueba — pero podría valer una nota en la documentación aclarando que la calidad de ese campo depende de la fuente elegida. | Minor / nota |
| `environment.yml` usa la sintaxis `pip: - -r file:requirements.txt` para instalar dependencias de pip dentro del entorno conda. Esta sintaxis es interpretada como una ruta absoluta de archivo (`file:///requirements.txt`) y falla con error 404, en vez de resolverse como ruta relativa al proyecto. En la práctica el impacto fue bajo, porque casi todos los paquetes de `requirements.txt` ya están duplicados en la lista principal de `environment.yml` y se instalan igual vía conda — pero al menos un paquete (`pip_system_certs`) quedó sin instalar automáticamente y hubo que agregarlo a mano con `pip install -r requirements.txt` después de crear el entorno. | Minor |
| `pyproject.toml` no declara una sección `[project]` con nombre, versión ni dependencias del paquete `healthcare_accessibility`. Esto hace que `pip install -e .` (paso indicado en la guía, sección 3.2) instale un paquete vacío llamado "UNKNOWN" en vez del paquete real, dejando además un residuo `src/UNKNOWN.egg-info`. Hubo que resolverlo agregando `src/` al `PYTHONPATH` manualmente en vez de depender de una instalación editable. | Minor — pero afecta directamente el primer paso de instalación documentado |
| El código en `data_processing_funcs.py:642` calcula áreas de superposición de polígonos (`boundary_intersections.geometry.area`) sin reproyectar a un CRS proyectado primero, generando el warning propio de geopandas: *"Geometry is in a geographic CRS. Results from 'area' are likely incorrect."* Esto es una imprecisión metodológica real (no solo un warning cosmético) en el cálculo de qué área administrativa "gana" una celda superpuesta. | Minor — vale la pena que el Developer lo revise, puede afectar la asignación de celdas en zonas de borde entre distritos |
| El pipeline Python exige explícitamente una columna llamada `id` en el archivo de facilities (a diferencia de R, donde es opcional). El CSV de healthsites.io trae `osm_id`, no `id` — hubo que renombrar la columna manualmente antes de poder correr `data_preparation.py`. Vale la pena que la documentación lo aclare more explícitamente. | Minor |
| `pop_travel_times.py` emite `RuntimeWarning: Some destination points could not be snapped to the street network` durante el cálculo de tiempos de viaje. El mensaje no cuantifica cuántos puntos quedaron sin conectar a la red vial, dificultando evaluar el impacto real en la cobertura de resultados. Sería valioso que el pipeline reporte el conteo o porcentaje de puntos afectados. | Minor |
| Mismo patrón de imprecisión de CRS que en `data_processing_funcs.py:642`, ahora en `geospatial_utils.py:1580-1581` — cálculo de centroides sin reproyectar a CRS proyectado primero, al generar los mapas de visualización. | Minor |
| El dashboard Python muestra en la leyenda de color del mapa los valores crudos de una escala log10 (ej. "-1.0, 0.6, 1.2, 2.8, 3.9") bajo el título "Estimated population (population, log10 scale)", en vez de mostrar la población real (des-transformada) o una escala más intuitiva. Un usuario sin conocimiento de escalas logarítmicas puede no entender qué representa un valor como "3.9". | Minor — afecta claridad de UX, no funcionalidad |
| El mapa a nivel "National" del dashboard Python arranca con un zoom inicial muy alejado, mostrando más territorio de países vecinos (Zambia, Mozambique) que del propio país seleccionado. No es un error, pero podría mejorarse ajustando el zoom inicial al bounding box del país. | Minor / sugerencia de UX |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | *(pendiente)* | |
| Technical accuracy | *(pendiente)* | |
| Prerequisite skills and knowledge | *(pendiente)* | |

### Structure and Organisation

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Headings and Subheadings | *(pendiente)* | |
| Logical Flow | *(pendiente)* | |
| Segmented content | *(pendiente)* | |
| Conciseness | *(pendiente)* | |

### Coherence

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Style Guide | *(pendiente)* | |
| Figure alignment | *(pendiente)* | |

### Accessibility

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Clarity | *(pendiente)* | |
| Terminology | *(pendiente)* | |
| Grammar and Spelling | *(pendiente)* | |
| Macros in spreadsheets | N/A — no aplica a esta Unidad | |

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices (style, naming, logic, hardcoded values) | *(pendiente — pendiente lectura de código fuente)* | *(pendiente)* | |
| Code documentation (comentarios, roxygen2/docstrings) | *(pendiente)* | *(pendiente)* | |
| Data management (datos sensibles, accesibilidad de inputs) | *(pendiente)* | *(pendiente)* | |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** — corrida completa `01_preprocess.R` + `02_ttm.R` con datos reales (Malawi): boundaries, facilities (healthsites.io), población (WorldPop), red de rutas construida (66.57s) y matriz de tiempo de viaje calculada (28.1s). Outputs `.csv` y `.parquet` generados correctamente. | ✅ **PASS** — `data_preparation.py` + `pop_travel_times.py` corridos con éxito (exit code 0 ambos) con datos reales de Malawi. Cálculo de tiempos de viaje: 75.64s. Outputs generados: `bicycle_travel_times_to_All healthcare facilities.parquet` (467KB) + 4 mapas HTML (nacional + 3 regiones). Falta ver el dashboard. | Evidencia completa en `data/ttm/malawi_closest_times.*` (R) y `outputs/malawi/*.parquet` + `outputs/malawi/maps/*.html` (Python) |
| Tested using alternative input data (para verificar que funciona con datos de otros usuarios) | ⏳ Parcial — se usaron datos reales de healthsites.io en vez de datos ficticios/de ejemplo, pero todavía no se probó con un segundo país/fuente distinta | *(pendiente)* | |
| Dependency management (librerías claras, memoria/procesamiento eficiente) | ✅ Dependencias documentadas correctamente en R User Guide; las 18 requeridas se instalaron sin fricción mayor (salvo conflicto de versión de `rlang`, resuelto reiniciando sesión) | *(pendiente)* | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Source code available, complies with QA checklist for code | *(pendiente)* | |
| README submitted, easy to follow | *(pendiente)* | |
| Interface clear and easy to understand | ✅ Confirmado visualmente (24/08, R) — controles de distrito, tipo de facility, distancia y grupo demográfico funcionan como documenta la Methodology. ✅ Confirmado también en Python (25/08) — mismos controles equivalentes (admin area, facility type, distance threshold, demographic group, show outside toggle, facility breakdown button) | |
| Expected outputs clearly communicated | ✅ Panel derecho muestra número de facilities, % de población fuera de rango, y población estimada más allá del umbral — coincide con la documentación en ambos workflows. ⚠️ Hallazgo en Python: la leyenda de color del mapa muestra valores crudos de log10 (ej. "3.9") en vez de población real o una escala más legible — puede confundir al usuario | Ver Proposed Amendments |
| Sensitive input data omitted/replaced | ✅ No sensitive data included (confirmado también por el propio Developer en Acceptance Criteria) | |
| Input data available to download | *(pendiente)* | |
| End-to-end test by Tester | ✅ **PASS** — dashboard R corrido y verificado visualmente con datos reales de Malawi (Central Region, 10 hospitales, 87% de población fuera de 8km). ✅ **PASS** — dashboard Python corrido y verificado visualmente con datos reales de Malawi (vista nacional, hospital, 10km, 82.7% de población fuera de rango, 24,117,974 personas estimadas más allá del umbral) | Ver capturas de sesión 24/08 y 25/08 |
| Tested with alternative input data | *(pendiente)* | |
| Compatible desktop/tablet/smartphone | *(pendiente — probado solo en desktop hasta ahora)* | |
| Runs independently of OS | ✅ Corrido en Windows sin problemas hasta ahora | |
| Memory/processing efficiency | ✅ Malawi (país chico) corrió rápido y sin errores de memoria; pendiente confirmar con Argentina (país grande) | |

### Audio and video Products

N/A — la Unidad no incluye contenido audiovisual.

### Knowledge check / Quiz Products

*(pendiente confirmar si la Unidad incluye quiz)*

---

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio — relevante para justificar cronograma si hace falta.
- No se encontró TdR de la Unidad; se trabaja asumiendo la idea original según documentación disponible.
- Malawi elegido como caso de control por ser el mismo que usó el Developer como prototipo — minimiza riesgo de que un fallo sea "por los datos" en vez de "por el código". Se reutilizó el mismo dataset de facilities (healthsites.io) en ambos workflows para comparación justa.
- Argentina, al ser un país grande, probablemente requiera boundaries ADM2 (no ADM1) y estrategia subnacional, según lo ya documentado por el Developer para casos como Bangladesh.
- Lección operativa: en la terminal Git Bash/mintty usada, copiar texto seleccionándolo puede disparar un Ctrl+C accidental si se usa esa combinación después, interrumpiendo procesos en curso sin aviso claro (exit code 130, sin traceback). Redirigir a un archivo de log y usar una segunda terminal para inspeccionar con `tail` evita el problema.
