# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 01/09/2026

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
- Dashboard Python confirmado visualmente con Malawi (vista nacional, hospital, 10km, 82.7% de población fuera de rango, 24,117,974 personas).
- **Sesión 01/09 — caso Argentina (pedido explícito del Developer):**
  - Entorno Python reconstruido en la misma notebook (se reprodujeron y reconfirmaron los bugs de `environment.yml` y `pyproject.toml`/"UNKNOWN" ya documentados el 24-25/08, esta vez con evidencia de traceback completo).
  - Workflow Python — `data_preparation.py` corrido con éxito para Argentina (los 5 outputs esperados confirmados).
  - Workflow Python — `pop_travel_times.py` **falló como estaba anticipado por el Developer**, con evidencia técnica precisa de la causa raíz (ver Proposed Amendments).
  - Dashboard Python — confirmado que falla de forma poco amigable (traceback crudo) cuando el parquet de tiempos de viaje no existe para el país configurado.
  - Workflow R — reconfirmado que el entorno sigue sano en la misma notebook (sin reinstalar nada). Dashboard R re-verificado con Malawi, con un hallazgo nuevo (mapa base no carga, ver Amendments).
  - Workflow R — se intentó reproducir el caso Argentina. Facilities de healthsites.io descargadas en CSV (no GeoJSON, por formato soportado en R). Confirmado que el cleaning code de R es insensible a mayúsculas/minúsculas en columnas (`rename_with(tolower)`), por lo que el desajuste `X`/`Y` vs `x`/`y` documentado no es un problema real.
  - Workflow R con Argentina — preprocesamiento (`01_preprocess.R`) en curso al momento de esta nota; pendiente confirmar resultado y continuar con `02_ttm.R` para ver si R reproduce el mismo límite de área que Python.
- Pendiente: resultado final de `01_preprocess.R` y `02_ttm.R` con Argentina en R, corrida subnacional (San Juan, pedido explícito del Developer), revisión de código fuente en detalle (estilo, comentarios, documentación de funciones) en R y Python — no realizada aún más allá de hallazgos puntuales encontrados al pasar.

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| El pipeline no crea automáticamente las carpetas de salida (`data/boundaries/`, `data/poi/`, `data/population/`, etc.). Si no existen previamente, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o dar un mensaje claro de qué falta. | Minor |
| La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real descargado de HDX trae `X`, `Y` en mayúscula, tanto para Malawi como para Argentina (reconfirmado 01/09 con un segundo país). El código de limpieza (`clean_healthcare_facilities`, vía `rename_with(tolower)`) maneja esto correctamente de forma deliberada — no es un problema funcional, solo una imprecisión de la documentación, que debería aclarar que el parser es insensible a mayúsculas/minúsculas. | Minor (documentación únicamente) |
| La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/error 500 en nuestra prueba. Se resolvió usando un archivo local de geoBoundaries como fallback (camino ya contemplado por la guía), pero vale la pena que el Developer sepa que la vía automática puede no ser confiable y ofrecer el fallback más explícitamente en la documentación. | Minor |
| El campo `ownership` aparece como `NA` en el popup del dashboard para varias facilities. No es un bug del código — el dato no viene completo en la fuente healthsites.io usada para esta prueba — pero podría valer una nota en la documentación aclarando que la calidad de ese campo depende de la fuente elegida. | Minor / nota |
| `environment.yml` usa la sintaxis `pip: - -r file:requirements.txt` para instalar dependencias de pip dentro del entorno conda. Esta sintaxis es interpretada como una ruta absoluta de archivo (`file:///requirements.txt`) y falla con error 404 (`ERROR: 404 Client Error: FileNotFoundError for url: file:///requirements.txt`), en vez de resolverse como ruta relativa al proyecto. Reconfirmado 01/09, con traceback completo, en un intento independiente de instalación en la misma notebook. Corrección: `- -r requirements.txt`, sin el prefijo `file:`. | Minor |
| `pyproject.toml` no declara una sección `[project]` con nombre, versión ni dependencias del paquete `healthcare_accessibility`. Esto hace que `pip install -e .` instale un paquete vacío llamado "UNKNOWN" en vez del paquete real. Reconfirmado 01/09. El import (`import healthcare_accessibility`) funciona igual porque el editable install mapea el path correctamente, pero el nombre incorrecto puede confundir en el futuro (ej. `pip show healthcare_accessibility` no lo encuentra). En Windows además requirió el workaround `SETUPTOOLS_USE_DISTUTILS=stdlib` + `--no-build-isolation` por un conflicto de `distutils`/`setuptools` no documentado en el troubleshooting de la guía. | Minor — pero afecta directamente el primer paso de instalación documentado |
| El código en `data_processing_funcs.py:642` calcula áreas de superposición de polígonos (`boundary_intersections.geometry.area`) sin reproyectar a un CRS proyectado primero, generando el warning propio de geopandas: *"Geometry is in a geographic CRS. Results from 'area' are likely incorrect."* Reconfirmado 01/09 con Argentina. Esto es una imprecisión metodológica real (no solo un warning cosmético) en el cálculo de qué área administrativa "gana" una celda superpuesta. | Minor — vale la pena que el Developer lo revise, puede afectar la asignación de celdas en zonas de borde entre distritos |
| El pipeline Python exige explícitamente una columna llamada `id` en el archivo de facilities (a diferencia de R, donde es opcional). El CSV/GeoJSON de healthsites.io trae `osm_id`, no `id` — el script lo renombra automáticamente (`process_healthsites_hcf_data`), pero solo si la columna de origen existe exactamente con ese nombre; no hay validación explícita si el esquema cambiara. Vale la pena que la documentación lo aclare más explícitamente. | Minor |
| `pop_travel_times.py` emite `RuntimeWarning: Some destination points could not be snapped to the street network` durante el cálculo de tiempos de viaje. El mensaje no cuantifica cuántos puntos quedaron sin conectar a la red vial, dificultando evaluar el impacto real en la cobertura de resultados. Sería valioso que el pipeline reporte el conteo o porcentaje de puntos afectados. | Minor |
| Mismo patrón de imprecisión de CRS que en `data_processing_funcs.py:642`, ahora en `geospatial_utils.py:1580-1581` — cálculo de centroides sin reproyectar a CRS proyectado primero, al generar los mapas de visualización. | Minor |
| El dashboard Python muestra en la leyenda de color del mapa los valores crudos de una escala log10 (ej. "-1.0, 0.6, 1.2, 2.8, 3.9") bajo el título "Estimated population (population, log10 scale)", en vez de mostrar la población real (des-transformada) o una escala más intuitiva. Un usuario sin conocimiento de escalas logarítmicas puede no entender qué representa un valor como "3.9". | Minor — afecta claridad de UX, no funcionalidad |
| El mapa a nivel "National" del dashboard Python arranca con un zoom inicial muy alejado, mostrando más territorio de países vecinos que del propio país seleccionado. No es un error, pero podría mejorarse ajustando el zoom inicial al bounding box del país. | Minor / sugerencia de UX |
| **[01/09]** `data_preparation.py` importa `importlib_metadata` (`from importlib_metadata import files`) sin declarar esta dependencia en `environment.yml` ni `requirements.txt`, causando `ModuleNotFoundError` al primer intento de ejecución. El objeto importado (`files`) no se usa en ningún lugar del script — es un import muerto que además genera una dependencia innecesaria no documentada. | Minor |
| **[01/09]** `health_data_source` está hardcodeado dentro de `data_preparation.py` (línea `health_data_source = "healthsites.io"  # "mwi_MHFR"`) en vez de ser un parámetro de `config.yaml`. Contradice el criterio "Hardcoded values… removed" marcado como "Yes" por el DP en la Acceptance Criteria Template — debería marcarse como **PARTIAL**, no "Yes". | Minor |
| **[01/09]** `acquire_latest_osm_data()` (en `osm_utils.py`) no valida `response.status_code` tras la descarga desde Geofabrik antes de guardar el archivo a disco. Un fallo de descarga (ej. URL de continente mal escrita, país no soportado) se guarda silenciosamente como si fuera válido, y el error real aparecería más adelante en el pipeline de forma confusa y sin relación aparente con la causa. | Minor |
| **[01/09]** `process_healthsites_hcf_data()` no aplica fallback de `healthcare` → `facility_type` cuando el tag `amenity` viene vacío, a diferencia de otra función del mismo repo (`convert_hcf_polygons_to_points`, en `osm_utils.py`) que sí lo hace. Facilities válidas con datos reales bajo el tag `healthcare` quedan sin tipo asignado, afectando el filtro por tipo del dashboard. Evidencia real encontrada en el geojson de Argentina (facility "Dharma": `amenity: ""`, `healthcare: "alternative"`). | Minor |
| **[01/09]** El método de instalación alternativo documentado en la Python User Guide (sección 3.3, plan B con `conda install` + `pip install -r requirements.txt`, usado cuando `environment.yml` falla) no instala `nbclient`/`jupyter`, requerido por Quarto para renderizar el dashboard. Error: `ModuleNotFoundError: No module named 'nbclient'`. Este problema solo aparece si se usa el plan B — está encadenado con el bug de `environment.yml` de arriba. | Minor |
| **[01/09] MAYOR:** `configs/config.yaml` (`analysis_crs`) asume un único EPSG proyectado por país. Esto es válido para países compactos (Nepal, Malawi, Rwanda, Suiza, etc.) pero **inadecuado para países grandes y multi-faja como Argentina**, donde el sistema geodésico oficial (POSGAR 2007) está dividido en 7 fajas (EPSG:5343-5349) precisamente porque ningún EPSG único cubre el territorio con precisión aceptable. Se usó EPSG:32720 (UTM zona 20S) como aproximación práctica para poder continuar el testeo — no es una solución real, solo permite avanzar. Facilities lejos del meridiano central (ej. San Juan, usado en nuestra prueba) tendrían distorsión de escala mayor a la de países con EPSG dedicado. La guía no ofrece ningún criterio para elegir `analysis_crs` en países grandes. | **Major** |
| **[01/09]** El dashboard Python no maneja con gracia la ausencia del archivo de tiempos de viaje (`outputs/<country>/bicycle_travel_times_to_All healthcare facilities.parquet`) cuando el pipeline previo no completó exitosamente. En vez de un mensaje claro, el usuario ve un `FileNotFoundError` crudo con traceback completo de Python. Confirmado con el caso Argentina (donde el parquet nunca se generó por el límite de área de r5). | Minor |
| **[01/09]** `data_preparation.py` no imprime ningún mensaje de confirmación al finalizar exitosamente — termina en silencio. Dificulta distinguir un final normal de una interrupción silenciosa (ej. por memoria), obligando a verificar manualmente el exit code o los archivos de salida. | Minor |
| **[01/09]** La documentación (R y Python) no especifica requisitos de memoria/hardware según tamaño de país o dataset (número de facilities, celdas de población, tamaño del archivo de entrada). Encaja en el criterio ya existente del Testing Recommendation Template: "Prerequisite skills and knowledge: are the resources needed clearly outlined?" — no cumplido. | Minor |
| **[01/09]** El dashboard R (Malawi, Central Region, hospital, 8km) no carga el mapa base — se ve el placeholder "API KEY REQUIRED" de CARTO tapando la geografía de fondo, en vez de un mapa de calles/relieve. Los marcadores de facilities y el polígono de población sí se renderizan bien. Sugiere una dependencia de API key de CARTO no configurada ni documentada en ningún lado de la R User Guide. | Minor-a-Mayor (afecta la orientación geográfica del usuario si no conoce el país) |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | Partial | Ver Amendment de `analysis_crs` — afecta la precisión de resultados en países grandes |
| Technical accuracy | *(pendiente)* | |
| Prerequisite skills and knowledge | **No** | No se especifican requisitos de memoria/hardware según tamaño de país (ver Amendments) |

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
| Good coding practices (style, naming, logic, hardcoded values) | *(pendiente — revisión de código fuente no realizada aún)* | **Partial** — hardcoded values: **No cumplido** (`health_data_source` hardcodeado en `data_preparation.py`). Naming/logic: sin revisar aún | Falta revisión formal de estilo en ambos lenguajes |
| Code documentation (comentarios, roxygen2/docstrings) | *(pendiente)* | **Partial** — se encontró un import muerto sin comentario explicativo (`importlib_metadata`) | |
| Data management (datos sensibles, accesibilidad de inputs) | ✅ Sin datos sensibles | ✅ Sin datos sensibles | No aplica — ambos usan datos públicos |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** — corrida completa `01_preprocess.R` + `02_ttm.R` con datos reales (Malawi): boundaries, facilities (healthsites.io), población (WorldPop), red de rutas construida (66.57s) y matriz de tiempo de viaje calculada (28.1s). Outputs `.csv` y `.parquet` generados correctamente. Reconfirmado sano el 01/09 sin reinstalar nada. | ✅ **PASS** (Malawi) — `data_preparation.py` + `pop_travel_times.py` corridos con éxito (exit code 0 ambos) con datos reales de Malawi (75.64s cálculo de tiempos). ✅ **PASS parcial** (Argentina) — `data_preparation.py` exitoso; `pop_travel_times.py` **FAIL esperado** por límite de área de r5 (ver Amendments) — comportamiento documentado por el propio DP, confirmado con evidencia técnica precisa | Evidencia en `data/ttm/malawi_closest_times.*` (R), `outputs/malawi/*` (Python), traceback de Argentina en Amendments |
| Tested using alternative input data (para verificar que funciona con datos de otros usuarios) | ✅ Parcial — probado con Argentina además de Malawi (segundo país, mismo tipo de fuente healthsites.io) | ✅ Parcial — ídem, Argentina probado además de Malawi | |
| Dependency management (librerías claras, memoria/procesamiento eficiente) | ✅ Dependencias documentadas correctamente en R User Guide; instalación sin fricción mayor (salvo conflicto de versión de `rlang`, resuelto reiniciando sesión) | **No cumplido** — `environment.yml` roto (bug de sintaxis) y método alternativo incompleto (falta `nbclient`); ver Amendments | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Source code available, complies with QA checklist for code | *(pendiente)* | |
| README submitted, easy to follow | *(pendiente)* | |
| Interface clear and easy to understand | ✅ Confirmado visualmente en R (24/08 y reconfirmado 01/09) y Python (25/08) — controles funcionan como documenta la Methodology en ambos workflows | ⚠️ Ver hallazgo de mapa base "API KEY REQUIRED" en R (01/09) |
| Expected outputs clearly communicated | ✅ Panel derecho coincide con la documentación en ambos workflows | ⚠️ Hallazgo en Python: leyenda log10 confusa. ⚠️ Hallazgo en Python: `FileNotFoundError` crudo cuando faltan datos de un país (Argentina) |
| Sensitive input data omitted/replaced | ✅ No sensitive data included (confirmado también por el propio Developer en Acceptance Criteria) | |
| Input data available to download | *(pendiente)* | |
| End-to-end test by Tester | ✅ **PASS** — dashboard R verificado con Malawi (Central Region, 10 hospitales, 87% fuera de 8km, 8,208,511 personas beyond, reconfirmado 01/09). ✅ **PASS** — dashboard Python verificado con Malawi (nacional, hospital, 10km, 82.7%, 24,117,974 personas) | Ver capturas de sesión 24/08, 25/08 y 01/09 |
| Tested with alternative input data | *(pendiente)* | |
| Compatible desktop/tablet/smartphone | *(pendiente — probado solo en desktop hasta ahora)* | |
| Runs independently of OS | ✅ Corrido en Windows sin problemas hasta ahora (más allá de los workarounds de instalación documentados en Amendments) | |
| Memory/processing efficiency | ✅ Malawi (país chico) corrió rápido y sin errores de memoria. ❌ **Argentina (país grande) — FAIL confirmado**: `pop_travel_times.py` falla con `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2` al intentar construir la red de r5. Confirma la limitación ya anticipada por el DP, con causa raíz más precisa (límite de diseño del motor r5, no "memory constraints" genérico como decía la Acceptance Criteria) | Traceback completo en sesión 01/09 |

### Audio and video Products

N/A — la Unidad no incluye contenido audiovisual.

### Knowledge check / Quiz Products

*(pendiente confirmar si la Unidad incluye quiz)*

---

## Pedidos específicos del Developer (Acceptance Criteria — "Requests for additional testing criteria")

| Pedido | Estado |
| --- | --- |
| **R and Python**: testear ambos workflows con las guías de usuario, reportar dificultades/bugs/errores | ✅ Hecho para ambos, con Malawi y Argentina. Hallazgos documentados en Proposed Amendments |
| **Subnational run**: probar el workflow subnacional en Argentina (una provincia), evaluar si el approach es aceptable y si la documentación alcanza | ⏳ **Pendiente — no iniciado aún** |
| **Main workflow**: correr el workflow principal para un país completo, notar dificultades | ✅ Hecho con Argentina (Python) — **FAIL esperado y confirmado** con evidencia técnica precisa (límite de área de r5). Pendiente confirmar en R (ver Testing Overview) |

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio — relevante para justificar cronograma si hace falta.
- No se encontró TdR de la Unidad; se trabaja asumiendo la idea original según documentación disponible.
- Malawi elegido como caso de control por ser el mismo que usó el Developer como prototipo — minimiza riesgo de que un fallo sea "por los datos" en vez de "por el código".
- Argentina fue el país elegido para cumplir el pedido explícito del Developer de correr un país grande. Confirmó exactamente el problema de memoria/área que el DP ya anticipaba.
- El intento de reproducir Argentina en R requirió convertir el archivo de facilities de GeoJSON (usado en Python) a CSV (formato soportado por R) — se optó por descargar el CSV directamente de HDX en vez de convertir programáticamente, evitando errores de manejo de geometrías mixtas (polígono/punto) en R.
- Lección operativa (01/09): en consolas tipo Anaconda Prompt/cmd, pegar comandos mientras la consola espera una confirmación previa (`Proceed? y/n`) hace que los comandos se concatenen y se interpreten mal. Escribir/pegar un comando por vez y esperar el retorno del prompt evita el problema.
- Lección operativa (01/09, distinta a la de Git Bash documentada antes): en Anaconda Prompt/cmd también se observó duplicación de texto al pegar comandos en algunos casos puntuales (ej. `set PATH=...` y `quarto --version` quedaron concatenados) — mismo síntoma que el problema de Git Bash ya documentado, pero en una terminal distinta. Tipear a mano en vez de pegar evita el problema en ambos casos.
