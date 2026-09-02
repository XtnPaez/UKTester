# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> **Nota de reconciliación (02/09/2026):** esta versión fue reconstruida
> revisando toda la sesión de testeo de punta a punta, para asegurar que
> ninguna nota, hallazgo o decisión de las sucesivas actualizaciones se
> perdiera al ir resumiendo. A partir de acá, las actualizaciones deben
> **agregar**, no reemplazar/condensar, las tablas existentes.
>
> Última actualización: 02/09/2026 (revisión de código Python agregada)

---

## ⚠️ Hallazgo más importante de toda la sesión — leer primero

**R y Python no son funcionalmente equivalentes.** Comparando el conteo de facilities procesadas para Malawi, mismo origen de datos (healthsites.io), con configuración idéntica de dashboard (Nacional, clinic, 10km, Total population):

| Tipo | R | Python | Diferencia |
| --- | --- | --- | --- |
| clinic | 48 | 67 | -19 (-28%) |
| dentist | 6 | 8 | -2 |
| doctors | 1 | 2 | -1 |
| hospital | 71 | 195 | **-124 (-64%)** |
| pharmacy | 26 | 27 | -1 |
| **Total** | **152** | **299** | **-147 (-49%)** |

Esto se propaga en cascada a los resultados de accesibilidad mostrados al usuario final:

| | R | Python |
| --- | --- | --- |
| % población fuera de rango | 84.1% | 76.1% |
| Población estimada más allá | 18.423.545 | 22.187.103 |

**Causa raíz: no determinada.** Se descartó que la diferencia de mayúsculas/minúsculas en columnas (`X`/`Y` vs `x`/`y`) sea la causa (el código R la maneja correctamente vía `rename_with(tolower)`). La cifra de "149 filas removidas por falta de coordenadas" (warning de R) es demasiado pequeña para explicar una diferencia de 147 facilities totales. Hipótesis no verificadas: los dos pipelines pudieron descargar snapshots distintos de healthsites.io/HDX en fechas distintas (R usa CSV, Python usa GeoJSON, descargados en sesiones separadas); o hay algún filtro adicional (ej. campo `completeness`, `operational_status`) aplicado por un lenguaje y no por el otro.

**Decisión de alcance:** se documenta este hallazgo con evidencia numérica exacta y reproducible, y se deja la investigación de causa raíz para que el Developer la resuelva en la próxima ronda — determinar por qué dos pipelines que leen la misma fuente llegan a conteos tan distintos requiere acceso al contexto interno del desarrollo que excede el alcance razonable de este ciclo de testing.

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide, Content Testing Quick Guide, Testing Recommendation Template |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — el hallazgo de paridad R/Python es candidato fuerte a definir esto como Rejected — major amendments)* |
| Reason for recommendation | *(pendiente)* |

## Testing Overview

- Tester: Cristian Páez (equipo Argentina).
- Documentación completa revisada antes de tocar código.
- **Bloqueante de acceso al repositorio de código: sin acceso del 12/08 al 19/08** (una semana completa de la fase de testing), por proceso de autorización SyOps pendiente. Resuelto el 19/08 vía equipo SIADS; clonado del repo confirmado exitoso el 20/08.
- No se encontró TdR (Términos de Referencia) de la Unidad; se trabaja asumiendo la idea original en base a la documentación disponible del Developer.
- Entorno técnico R instalado y verificado en notebook sin permisos de administrador: R 4.4.0, Java 21 (vía rJavaEnv), Quarto 1.9.38 (portable). Reconfirmado sano el 01/09 sin necesidad de reinstalar nada.
- **Pipeline R corrido end-to-end con datos reales (Malawi, 24/08, reconfirmado 01/09):**
  - `01_preprocess.R`: boundaries (geoBoundaries ADM1), facilities (healthsites.io vía HDX, 149 filas sin coordenadas descartadas automáticamente — comportamiento esperado), 6 rasters demográficos de WorldPop + stack combinado.
  - `02_ttm.R`: red de rutas construida en 66.57s, matriz de tiempo de viaje en 28.1s. Outputs `malawi_closest_times.csv` (~95MB) y `.parquet` (~13MB).
- **Dashboard R confirmado visualmente (24/08, reconfirmado 01/09):** `quarto preview` levantó sin errores. Probado con Central Region: 10 hospitales, 87% de población fuera de 8km, 8.208.511 personas estimadas más allá del umbral, popups funcionando. Campo `ownership` aparece como `NA` para varias facilities (calidad de dato de fuente, no bug).
- Entorno técnico Python resuelto vía Miniconda (modo "Just Me", sin admin). Se intentó primero evitar conda (venv + pip), pero se pivotó a Miniconda al encontrar que `cykhash` (dependencia de `pyrosm`) no publica wheels precompilados para Windows en PyPI — solo vía conda-forge.
- **`data_preparation.py` y `pop_travel_times.py` corridos end-to-end con éxito (Malawi, 25/08):** exit code 0 ambos. Tiempos comparables a R (75.64s cálculo de tiempos). Outputs: parquet + 4 mapas HTML.
- **Dashboard Python confirmado visualmente (25/08):** `quarto render` + `shiny run` funcionaron sin errores. Vista nacional, hospital, 10km: 82.7% fuera de rango, 24.117.974 personas beyond.
- Se reutilizó el mismo tipo de fuente (healthsites.io) para Malawi y Argentina, en ambos lenguajes, buscando comparaciones consistentes.

### Sesión 01/09 — caso Argentina, workflow nacional (pedido explícito del Developer)

- Entorno Python reconstruido en la misma notebook desde cero; reproducidos y reconfirmados con evidencia completa (traceback) los bugs de `environment.yml` y `pyproject.toml` ya conocidos.
- Soporte para Argentina agregado manualmente: `country_continent_dict["Argentina"] = "south-america"` (con guión, formato exigido por la URL de Geofabrik — no documentado explícitamente); `analysis_crs["Argentina"]` agregado (ver hallazgo Mayor de CRS más abajo).
- Facilities de Argentina descargadas de healthsites.io/HDX en GeoJSON (15.576 features); confirmado que la columna crítica `osm_id` está presente (no se repitió el riesgo de `KeyError` que habíamos anticipado).
- Python `data_preparation.py`: exitoso para Argentina (5 outputs confirmados).
- Python `pop_travel_times.py`: **FAIL esperado y confirmado** — `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2`. Confirma el problema ya anticipado por el DP en la Acceptance Criteria, pero con causa técnica más precisa (límite de diseño del motor r5, no "memory constraints" genérico como dice el texto del DP).
- Dashboard Python: confirmado que no maneja con gracia la ausencia del parquet de tiempos de viaje — `FileNotFoundError` crudo con traceback completo, en vez de un mensaje claro al usuario.
- R `02_ttm.R` (workflow nacional, rama `main`): **tres intentos independientes**, todos detenidos en apariencia en el mismo punto ("Attaching district names..."), sin fallar ni terminar durante horas (uno de ellos 4+ horas). Ningún intento terminó por sí solo — requirió corte manual con severidad creciente entre intentos (uno vía suspensión accidental de la notebook, uno vía botón "Stop" de la interfaz, uno vía cierre forzado del proceso a nivel de sistema operativo, porque ni `Ctrl+C` ni el botón Stop respondieron). **Investigado y corregido:** el proceso sí estaba avanzando, solo muy lento — la apariencia de "colgado" en al menos un caso se debía a que la ventana de RGui había dejado de repintarse visualmente bajo presión de memoria del sistema (resuelto con "Ventanas → Cascada", forzando el repintado; el proceso seguía vivo, confirmado por actividad de CPU/disco en el Administrador de Tareas). El intento nacional real, cuando finalmente llegó a la etapa de construcción de red, **falló con el mismo tipo de error de límite de área que Python**: `Error in r5r::build_network(): Geographic extent of street layer exceeds limit of "975,000" km^2` — el mismo límite exacto (975.000 km²), confirmando que ambos lenguajes comparten el motor subyacente (r5/r5r vs r5py) y su límite de diseño. La diferencia real es de **eficiencia y feedback al usuario**: Python falla en segundos con causa clara; R tarda del orden de horas en llegar al mismo resultado, sin ningún chequeo temprano ni indicador de progreso intermedio.

### Sesión 01/09 — caso Argentina, workflow subnacional (pedido explícito del Developer)

- **Aclaración de atribución del pedido:** la Acceptance Criteria Template pide una corrida subnacional en Argentina sin especificar una provincia particular (*"for example, one province"*). El propio ejemplo de referencia del Developer, en `docs/R/03a-subnational-workflow.md`, usa **Buenos Aires**. **San Juan fue decisión del Tester**, no instrucción del Developer — elegida por conveniencia práctica (facilities de muestra ya confirmadas ahí desde la revisión inicial del geojson de Argentina, y para evitar depender de fuentes de boundaries adicionales como GADM/Natural Earth que pide el ejemplo de Buenos Aires).
- Se identificó que el Developer provee un workflow subnacional específico para R en la rama de git `r-subnational-workflow` (mencionada solo de pasada en la Acceptance Criteria Template), con documentación dedicada en `docs/R/03a-subnational-workflow.md`, **marcada como "(WIP)" por el propio Developer** en el título del documento.
- **Hallazgos de la lectura de esa documentación (antes de intentar ejecutarla):**
  - Requiere `osmium-tool`, una dependencia nueva no mencionada en ningún lado de los prerequisitos de instalación principal de la R User Guide.
  - Requiere trabajo manual en QGIS para filtrar boundaries (*"In QGIS, filter to keep only municipalities with province = ..."*) — no es un paso scripteado.
  - Inconsistencia de fuente de boundaries: el workflow país-completo usa geoBoundaries; el documento subnacional en cambio indica descargar de **GADM o Natural Earth**, sin explicar el cambio.
  - El comando de ejemplo de `osmium extract` en el walkthrough combina recorte por polígono (`-p`) **y** por bounding box (`-b`) en la misma llamada, sin aclarar si es intencional.
- Boundaries de San Juan preparadas: **el filtrado simple por nombre de texto falló** (0 resultados — "San Juan" no existe como nombre de departamento ADM2, solo como nombre de provincia ADM1). **El filtrado por `st_intersects` geométrico también falló** — trajo 28 resultados en vez de los 19 departamentos reales, incluyendo departamentos de provincias vecinas (La Rioja, Mendoza, San Luis) que solo tocan el borde. **El método correcto (centroide del departamento dentro del polígono de la provincia)** dio los 19/19 exactos — este método no está documentado en ningún lado de `03a-subnational-workflow.md`, que solo dice "filtrar" sin detallar cómo.
- PBF recortado con `osmium-tool` (ya estaba instalado, no hizo falta instalarlo) — 984 KB, contra 428 MB del país completo.
- **Primer intento con la config subnacional armada, sobre la rama `main`, dio el mismo error de límite de área que el caso nacional.** Investigado: `02_ttm.R` en `main` **no lee `network_source_path`, `analysis_mode` ni `subnational_area` en absoluto** — siempre descarga y usa el PBF del país completo, ignorando por completo la configuración subnacional.
- Comparando el código fuente de `02_ttm.R` entre `main` y `origin/r-subnational-workflow`, se confirmó que la rama subnacional sí implementa la lógica correcta (`format_config()`, `validate_config()`, `define_area_name()`, uso condicional de `network_source_path`).
- Se hizo checkout de la rama `r-subnational-workflow` (con `git stash` previo para no perder la configuración de Argentina hecha sobre `main`). Resolución de conflictos de merge: ambos `config.yaml` a favor de la configuración de Argentina/San Juan ya armada; conflicto de tipo "modify/delete" en `data_preparation.py` (ese archivo **no existe** en la rama `r-subnational-workflow` — confirma que esa rama es anterior a que se agregara el código Python al repo), resuelto con `git rm`.
- **Con el código correcto, el workflow subnacional para San Juan corrió exitosamente:** `01_preprocess.R` completó sin error (boundaries escritas correctamente como `san_juan_districts.geojson`, no `argentina_districts.geojson` — a diferencia del comportamiento en `main`, ver Amendments); `02_ttm.R`: red construida en **4.18 segundos**, accesibilidad calculada en **1.69 segundos**, outputs generados correctamente. Confirmado el log `"Using provided network source file: data/network/san_juan/san_juan.osm.pbf"`.
- **Conclusión: el approach subnacional en sí es aceptable y funciona bien y de forma eficiente** una vez en la rama correcta. El problema real es de **organización/descubribilidad del repositorio** (rama nunca mergeada a `main`, y desactualizada respecto a ella — le falta todo el árbol de código Python agregado después, incluyendo `postprocessing.py`, confirmado al intentar por error correr el dashboard Python desde esa rama). Un usuario que siga solo la R User Guide principal nunca descubriría esta rama por sí solo — se menciona únicamente de pasada en la Acceptance Criteria Template del Developer.

### Sesión 01/09 (noche) — comparación de paridad R vs Python con Malawi

- Se configuraron ambos dashboards con el mismo filtro exacto para comparación justa: Nacional, clinic, 10km, Total population. (Nota metodológica: el primer intento comparó configuraciones no equivalentes — R con "Northern Region" + filtro "doctors" inexistente en los datos, dando 0 facilities/100% trivial; corregido a nivel Nacional en ambos para evitar comparar una región completa de R contra un distrito ADM2 de Python, que no son la misma unidad geográfica.)
- **Hallazgo crítico ya descripto arriba**: diferencia de ~49% en facilities procesadas.
- Al intentar el dashboard Python: la interfaz se ve visiblemente distinta a R en estilo — esto coincide con lo que el propio Developer ya declaró en la Acceptance Criteria (*"the Python dashboard is yet to have the styling applied"*), no es un hallazgo nuevo.
- **Hallazgo:** la página del dashboard Python quedó "pálida"/sin responder (patrón de desconexión de WebSocket de Shiny); resuelto con recarga (F5/Ctrl+F5). **Hallazgo adicional:** la recarga reseteó el filtro de tipo de facility al valor por defecto ("hospital") en vez de preservar la selección del usuario ("clinic") — no mantiene estado de sesión ante una reconexión.
- **Hallazgo:** el botón "Show health facility breakdown" del dashboard Python no responde a clicks — sin error en la consola del navegador (F12) ni actividad nueva en el log del servidor Shiny al presionarlo. Confirmado tras verificar que no era un problema de scroll ni de renderizado fuera de vista.
- **Hallazgo:** `www/whiteAAlogo.png` retorna 404 repetidamente en los logs del servidor Python — asset faltante (probablemente el logo de Analysis for Action).
- Ante el botón roto, el conteo de facilities se obtuvo directamente vía código (`gpd.read_file(...).value_counts()` en Python; `table(facilities$type)` en R) en vez de depender de la UI — de ahí sale la tabla del hallazgo crítico.

### Sesión 02/09 — revisión de código fuente en R (11 archivos, `src/r/dashboard/R/`)

Ver detalle completo en Amendments. Resumen: calidad general buena (manejo de errores robusto — reintentos con backoff en Overpass, validación MD5 en descargas, chequeos de existencia de directorios; roxygen2 presente en casi todas las funciones exportadas). Hallazgos: causa raíz confirmada del bug de mapa base (falta de API key de CARTO); patrón sistemático de docstrings roxygen2 desactualizados respecto a valores default reales del código (2 casos confirmados + 1 caso de copy-paste); una asimetría positiva a favor de R en el manejo de descargas de OSM (índice Geofabrik dinámico vs diccionario hardcodeado en Python); una función embrionaria (`find_crs()`) que podría ser punto de partida para resolver el problema de EPSG único en países multi-faja; y un bug de mensaje de log copy-pasteado en el `02_ttm.R` de la rama subnacional.

**Pregunta abierta, no resuelta:** existe una carpeta `src/healthcare_accessibility/experimental/` (10 archivos Python) cuyo propósito no está claro ni documentado en ninguna guía — no se investigó su contenido en profundidad. Vale la pena preguntarle al Developer qué es y si debería estar en el repo público de esta forma.

**Pendiente:** confirmar si existe un archivo `DESCRIPTION` en `src/r/dashboard/` (un nivel arriba de la carpeta `R/` que sí se revisó) — la R User Guide lo menciona como fuente para `devtools::install_deps()`; no se confirmó su existencia en esta sesión porque solo se subió la subcarpeta `R/` para revisión, no la carpeta padre completa.

### Sesión 02/09 (continuación) — revisión de código fuente en Python (`data_processing_funcs.py`, `geospatial_utils.py`, `postprocessing.py`, `pop_travel_times.py`, `utils.py`, `accessability_metrics.py`, `fix_quarto_static_assets.py`)

- **Hallazgo de bug real:** `clean_gdf_boundaries()` (en `geospatial_utils.py`) tiene 6 condiciones `if/elif` con la forma `"NAME_1" and "ID_1" in gdf` — un error de precedencia de operadores en Python: un string no vacío como `"NAME_1"` siempre es `True`, así que la condición nunca verifica realmente si esa columna existe, colapsando al último chequeo (`"ID_1" in gdf`). Se repite en las 6 ramas de la función. Funciona "por casualidad" para nuestro caso real (geoBoundaries), pero está roto para los demás formatos que dice soportar (DIVA GIS, GADM), con una inconsistencia interna adicional en la rama ADM2-GADM (verifica `GID_2` pero renombra `NAME_2`, no `NAME_1`).
- **Pista de código para el hallazgo crítico de paridad (Amendment #1):** `process_healthsites_hcf_data()` (la función real usada en el pipeline Python) **no filtra ninguna facility por coordenadas faltantes** — solo renombra columnas y descarta duplicados por `id`. R sí filtra explícitamente (149 filas removidas, mensaje de warning). Hipótesis con evidencia de código: el CSV de HDX (usado por R) puede incluir filas con celdas de coordenadas vacías que luego se descartan; el GeoJSON (usado por Python) probablemente solo exporta features con geometría ya válida — los dos formatos de descarga podrían no ser snapshots directamente equivalentes del mismo dataset de origen. No confirmado, pero es la pista más concreta encontrada hasta ahora para la investigación que le corresponde al Developer.
- **Inconsistencia interna en Python** (no solo "R vs Python"): `get_data_from_web()` (usada para WorldPop y geoBoundaries) sí valida `response.raise_for_status()`; `acquire_latest_osm_data()` (usada para OSM/Geofabrik, ya documentada en Amendment #21) no lo hace — dos patrones de manejo de descargas conviviendo en el mismo código.
- Confirmada la ubicación exacta del hallazgo de CRS ya documentado (Amendment #16): `generate_folium_travel_map()`, líneas 1580-1581, calcula el centroide **después** de reproyectar a `visualisation_crs` (geográfico). El mismo archivo también genera los mapas HTML estáticos de travel-time con leyenda en escala log10 sin des-transformar — el mismo patrón de UX confuso del Amendment #17 se repite acá, no es exclusivo del dashboard interactivo.
- Código muerto/confuso (no funcional, solo claridad): en `generate_folium_travel_map()`, un `.sort_values(ascending=True)` sobre una columna cuyo resultado se descarta al reasignarse (pandas realinea por índice) — no tiene efecto real, solo confunde a quien lea el código.
- Confirmado sin discrepancia: `max_bicycle_traffic_stress=4` hardcodeado en `evaluate_travel_times_to_facilities()`, consistente con el `max_lts = 4L` de R (Amendment ya documentado como comportamiento esperado en ambos lenguajes).
- `fix_quarto_static_assets.py`: script de utilidad no documentado en ninguna guía, que parchea manualmente assets estáticos generados por Quarto en el `app.py` del dashboard — sugiere que el propio Developer conoce fricciones en el proceso de build del dashboard (relacionado posiblemente con el Amendment #23 de `nbclient` faltante).
- Carpeta `experimental/` (10 archivos Python): sigue sin investigarse en detalle — pregunta abierta para el Developer.

- Revisión de código fuente en Python: **completada** (archivos principales).
- Investigación de causa raíz de la discrepancia de facilities: dejada conscientemente para el Developer, aunque la revisión de código Python aportó una hipótesis concreta (ver nota bajo el Amendment crítico #1 en Proposed Amendments).
- Unit tests de Python: pendiente confirmar estado (la Acceptance Criteria ya admite que no existen; falta verificación independiente).
- Otros modos de transporte (WALK, CAR): pendiente, solo se probó BICYCLE (default) en ambos lenguajes.
- Fuente alternativa de facilities (ej. registro oficial de Malawi vía `get_healthcare_facilities_malawi` en R): pendiente, solo se usó healthsites.io en todos los casos.
- Compatibilidad multi-dispositivo: no testeado, pero aceptable sin más trabajo — el Developer ya declaró explícitamente en la Acceptance Criteria que recomienda uso en desktop.

## Proposed Amendments

| # | Amendment description | Major / minor |
| --- | --- | --- |
| 1 | **CRÍTICO: R y Python procesan un número de facilities radicalmente distinto para el mismo país (Malawi) y el mismo tipo de fuente: 152 vs 299 total (~49% de diferencia), con hospital como categoría más afectada (71 vs 195, -64%). Se propaga a los resultados de accesibilidad mostrados al usuario. Causa raíz no determinada.** | **Major (crítico)** |
| 2 | `analysis_crs` (Python) asume un único EPSG proyectado por país — inadecuado para países grandes multi-faja como Argentina (POSGAR 2007 dividido en 7 fajas oficialmente por esta razón). Se usó EPSG:32720 (UTM 20S) como aproximación práctica, no solución real. La guía no ofrece criterio para elegir `analysis_crs` en países grandes. | **Major** |
| 3 | El workflow nacional en R (`02_ttm.R`, rama `main`) no tiene chequeo temprano de extensión geográfica antes de construir la red — a diferencia de Python, que falla en segundos. Con Argentina completa, el proceso tarda del orden de horas en llegar al mismo error de límite de área (975.000 km²), sin ningún indicador de progreso. | **Major** |
| 4 | El workflow subnacional para R (`analysis_mode: subnational`, `network_source_path`, `subnational_area`) está implementado en la rama `r-subnational-workflow`, nunca mergeada a `main` y desactualizada respecto a ella (falta, por ejemplo, todo el árbol de código Python agregado después). La R User Guide principal no advierte en ningún lugar destacado que hace falta cambiar de rama completa. **Una vez en la rama correcta, la funcionalidad en sí funciona bien y de forma eficiente** — el problema es de organización/descubribilidad del repositorio, no de la lógica implementada. | **Major** (gestión de repo, no de funcionalidad) |
| 5 | El botón "Show health facility breakdown" del dashboard Python no responde a clicks — sin error en consola de navegador ni actividad en el log del servidor. | Minor-a-Mayor |
| 6 | El mapa base del dashboard R no carga — placeholder "API KEY REQUIRED" de CARTO. **Causa raíz confirmada en revisión de código:** `dashboard_map.R` llama a `leaflet::addProviderTiles("CartoDB.Positron")` sin API key configurada; CARTO ahora la exige para ese proveedor. | Minor-a-Mayor |
| 7 | El pipeline no crea automáticamente las carpetas de salida necesarias; si no existen, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o avisar claramente. | Minor |
| 8 | La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real trae `X`, `Y` en mayúscula, confirmado con Malawi y Argentina. El código de limpieza (`rename_with(tolower)`) lo maneja correctamente de forma deliberada — es solo imprecisión de la documentación, no un riesgo funcional. | Minor (documentación) |
| 9 | La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/error 500 en nuestra prueba. Se resolvió con geoBoundaries local (fallback ya contemplado por la guía), pero vale la pena advertir más explícitamente que la vía automática puede no ser confiable. | Minor |
| 10 | El campo `ownership` aparece como `NA` en el popup del dashboard para varias facilities. No es un bug de código — el dato no viene completo en la fuente healthsites.io — pero podría valer una nota en la documentación aclarando que la calidad de ese campo depende de la fuente elegida. | Minor / nota |
| 11 | `environment.yml` usa la sintaxis `pip: - -r file:requirements.txt`, interpretada como ruta absoluta de archivo (`file:///requirements.txt`), falla con error 404 en vez de resolverse como ruta relativa. Reconfirmado 01/09 con traceback completo, en un intento de instalación independiente. Corrección: `- -r requirements.txt`, sin el prefijo `file:`. Impacto práctico bajo en el primer hallazgo (24/08) porque casi todos los paquetes de `requirements.txt` estaban duplicados en `environment.yml`, salvo `pip_system_certs`, que quedó sin instalar automáticamente. | Minor |
| 12 | `pyproject.toml` no declara una sección `[project]` con nombre/versión/dependencias del paquete `healthcare_accessibility`. Esto hace que `pip install -e .` instale un paquete vacío llamado "UNKNOWN" en vez del real (deja además un residuo `src/UNKNOWN.egg-info`). El import funciona igual porque el editable install mapea el path correctamente, pero el nombre incorrecto puede confundir (ej. `pip show healthcare_accessibility` no lo encuentra). Reconfirmado 01/09; en Windows además requirió el workaround `SETUPTOOLS_USE_DISTUTILS=stdlib` + `--no-build-isolation` por un conflicto de `distutils`/`setuptools`, no documentado en el troubleshooting de la guía. | Minor — pero afecta el primer paso de instalación documentado |
| 13 | `data_processing_funcs.py:642` calcula áreas de superposición de polígonos (`boundary_intersections.geometry.area`) sin reproyectar a un CRS proyectado primero, generando el warning de geopandas *"Geometry is in a geographic CRS. Results from 'area' are likely incorrect."* Esto es una imprecisión metodológica real (no solo cosmética) en el cálculo de qué área administrativa "gana" una celda superpuesta. Reconfirmado con Argentina. | Minor — puede afectar la asignación de celdas en zonas de borde entre distritos |
| 14 | El pipeline Python exige explícitamente una columna llamada `id` en el archivo de facilities (a diferencia de R, donde es opcional). El CSV/GeoJSON de healthsites.io trae `osm_id`, no `id` — el script lo renombra automáticamente, pero no valida explícitamente si el esquema de origen cambiara. Vale la pena que la documentación lo aclare más explícitamente. | Minor |
| 15 | `pop_travel_times.py` emite `RuntimeWarning: Some destination points could not be snapped to the street network` sin cuantificar cuántos puntos, dificultando evaluar el impacto real en la cobertura. Mismo patrón de ambigüedad en R: `"No travel times returned for facility type 'dentist'"` en el caso subnacional de San Juan, sin distinguir si es porque no hay facilities de ese tipo en el área (normal) o porque existen pero no conectaron a la red (más preocupante). | Minor |
| 16 | Mismo patrón de imprecisión de CRS sin reproyectar que el Amendment #13, ahora en `geospatial_utils.py:1580-1581` — cálculo de centroides al generar los mapas de visualización. | Minor |
| 17 | El dashboard Python muestra en la leyenda de color del mapa los valores crudos de una escala log10 (ej. "-1.0, 0.6, 1.2, 2.8, 3.9") bajo el título "Estimated population (population, log10 scale)", en vez de población real (des-transformada) o una escala más intuitiva. Un usuario sin conocimiento de escalas logarítmicas puede no entender qué representa un valor como "3.9". | Minor — afecta claridad de UX, no funcionalidad |
| 18 | El mapa a nivel "National" del dashboard Python arranca con un zoom inicial muy alejado, mostrando más territorio de países vecinos (Zambia, Mozambique) que del propio país seleccionado. Podría mejorarse ajustando el zoom inicial al bounding box del país. | Minor / sugerencia de UX |
| 19 | `data_preparation.py` importa `importlib_metadata` (para usar `files`, que nunca se usa en el script) sin declarar esta dependencia en `environment.yml` ni `requirements.txt`, causando `ModuleNotFoundError` al primer intento de ejecución. Import muerto que además genera una dependencia innecesaria no documentada. | Minor |
| 20 | `health_data_source` está hardcodeado dentro de `data_preparation.py` (línea `health_data_source = "healthsites.io"  # "mwi_MHFR"`) en vez de ser un parámetro de `config.yaml`. Contradice el criterio "Hardcoded values… removed" marcado como "Yes" por el DP en la Acceptance Criteria Template — debería marcarse como **PARTIAL**, no "Yes". | Minor |
| 21 | `acquire_latest_osm_data()` (en `osm_utils.py`) no valida `response.status_code` tras la descarga desde Geofabrik antes de guardar el archivo a disco. Un fallo de descarga se guarda silenciosamente como si fuera válido, y el error real aparecería más adelante en el pipeline de forma confusa. | Minor |
| 22 | `process_healthsites_hcf_data()` no aplica fallback de `healthcare` → `facility_type` cuando el tag `amenity` viene vacío, a diferencia de otra función del mismo repo (`convert_hcf_polygons_to_points`, en `osm_utils.py`) que sí lo hace. Facilities válidas con datos reales bajo el tag `healthcare` quedan sin tipo asignado, afectando el filtro por tipo del dashboard. Evidencia real en el geojson de Argentina (facility "Dharma": `amenity: ""`, `healthcare: "alternative"`). | Minor |
| 23 | El método de instalación alternativo documentado en la Python User Guide (sección 3.3, plan B con `conda install` + `pip install -r requirements.txt`, usado cuando `environment.yml` falla) no instala `nbclient`/`jupyter`, requerido por Quarto para renderizar el dashboard. Este problema solo aparece si se usa el plan B — está encadenado con el Amendment #11. | Minor |
| 24 | El dashboard Python no maneja con gracia la ausencia del archivo de tiempos de viaje cuando el pipeline previo no completó exitosamente. En vez de un mensaje claro, el usuario ve un `FileNotFoundError` crudo con traceback completo de Python. Confirmado con el caso Argentina nacional. | Minor |
| 25 | `data_preparation.py` y `01_preprocess.R` no imprimen ningún mensaje de confirmación al finalizar exitosamente — ambos terminan en silencio. Dificulta distinguir un final normal de una interrupción silenciosa, obligando a verificar manualmente el exit code o los archivos de salida. | Minor |
| 26 | La documentación (R y Python) no especifica requisitos de memoria/hardware según tamaño de país o dataset (número de facilities, celdas de población, tamaño del archivo de entrada). Encaja en el criterio ya existente del Testing Recommendation Template: "Prerequisite skills and knowledge: are the resources needed clearly outlined?" — no cumplido. La Python User Guide da una pista indirecta solo en una tabla de tiempos de ejecución (Nepal "Requires >5.6GB RAM", Bangladesh "Memory errors observed at national scale"), no como requisito documentado explícitamente. | Minor |
| 27 | El filtrado de boundaries a un área subnacional por nombre de texto (`grepl` contra `shapeName`) es insuficiente porque existen departamentos homónimos en distintas provincias argentinas (ej. "25 de Mayo", "9 de Julio" aparecen en varias provincias). Un filtro por `st_intersects` geométrico también es insuficiente porque incluye departamentos vecinos que solo tocan el borde. El método correcto (centroide dentro del polígono provincial) no está documentado en `03a-subnational-workflow.md`, que solo dice "filter to keep only municipalities within [área]" sin detallar cómo. | Minor |
| 28 | `01_preprocess.R`, en la rama `main`, al pasar de modo `country` a `subnational` reusando la misma carpeta de proyecto, sobrescribió el archivo `argentina_districts.geojson` del intento nacional anterior sin avisar (mismo nombre base, ya que en `main` el nombre de archivo siempre usa el país, no el área). En la rama `r-subnational-workflow` este problema no se repite (usa `<area>_districts.geojson`). | Minor / nota |
| 29 | Recargar la página del dashboard Python (tras una desconexión de WebSocket, patrón visible como pantalla "pálida"/congelada) resetea los filtros del usuario a los valores por defecto en vez de preservar la sesión/selección — se pierde el estado del usuario. | Minor |
| 30 | Asset faltante: `www/whiteAAlogo.png` retorna 404 repetidamente en los logs del servidor del dashboard Python (probablemente el logo de Analysis for Action). | Minor |
| 31 | `docs/R/03a-subnational-workflow.md` está marcado como "(WIP)" por el propio Developer en el título, requiere una herramienta externa nueva no mencionada en la instalación principal (`osmium-tool`), pide trabajo manual en QGIS (no scripteado), y usa una fuente de boundaries distinta (GADM/Natural Earth) a la del resto del proyecto (geoBoundaries) sin explicar el cambio. Ver también Amendment #4 y #27. | Minor (documentación, parte del cuadro del Amendment #4) |
| 32 | **[R, revisión de código]** Docstring desactualizado: `compute_closest_accessibility()` (en `compute_closest_accessibility.R`) documenta en el roxygen2 que `max_travel_time` tiene default 120 minutos, pero el valor real del parámetro en el código es 167 (la R User Guide externa sí dice 167 correctamente — es la documentación *interna* del código la que quedó desactualizada). | Minor |
| 33 | **[R, revisión de código]** Mismo patrón: `get_osm_districts()` (en `get_districts.R`) documenta en el roxygen2 que `timeout_seconds` tiene default 120, pero el código real usa 300. | Minor |
| 34 | **[R, revisión de código]** Copy-paste de documentación: el docstring completo de `download_worldpop()` (en `get_population_subgroups.R`) es una copia literal del de `get_subgroup_population_files()` (describe extracción de zip y revisión de carpetas de destino), pero `download_worldpop()` en realidad solo descarga el archivo, no lo extrae ni revisa carpetas. | Minor |
| 35 | **[R, revisión de código] Patrón general:** los Amendments #32, #33 y #34 sugieren que cuando cambian valores por defecto en el código, no se actualiza la documentación roxygen2 correspondiente — es un patrón sistemático de mantenimiento de documentación, no errores aislados. | Minor (patrón) |
| 36 | **[R, revisión de código]** En `02_ttm.R` de la rama `r-subnational-workflow`, el mensaje de log es idéntico ("Using country-level population raster: ...") tanto en la rama `if (config$analysis_mode == "country")` como en la rama `else if (config$analysis_mode == "subnational")` del código — un copy-paste que hace que el log diga "country-level" incluso cuando en realidad está usando el raster recortado del área subnacional (confirmado en el log real de la corrida de San Juan: *"Using country-level population raster: .../san_juan_agesex_2025/geodemographics.tif"*). Mensaje engañoso, no afecta el resultado, solo la claridad del log. | Minor |

**Nota positiva / recomendación cruzada [R, revisión de código]:** `download_geofabrik_pbf()` en R resuelve URLs de país consultando el **índice JSON en vivo de Geofabrik** (`get_geofabrik_index()` → `resolve_geofabrik_pbf_url()`), evitando el problema de diccionario hardcodeado que causó el bug de Python del Amendment relacionado a `country_continent_dict` ("south-america" vs "south_america" para Argentina). Además valida MD5 tras la descarga. Se recomienda que Python adopte un enfoque similar en lugar de mantener un diccionario manual país→continente.

**Nota / posible pista de solución [R, revisión de código]:** `add_district_to_points.R` incluye una función `find_crs()` que auto-selecciona una proyección UTM según el centroide del país/área — un enfoque embrionario al mismo problema del Amendment #2 (EPSG único en países multi-faja). Actualmente solo se usa para el método de asignación `raster`, no para el cálculo de travel-time en sí, pero podría ser un punto de partida útil para que el Developer resuelva el problema de forma más general.

| # | Amendment description | Major / minor |
| --- | --- | --- |
| 37 | **[Python, revisión de código]** `clean_gdf_boundaries()` tiene un bug de precedencia de operadores en Python: 6 condiciones de la forma `"NAME_1" and "ID_1" in gdf` nunca verifican realmente la primera columna (un string no vacío siempre es `True`), colapsando al último chequeo. Funciona por casualidad para el formato geoBoundaries (nuestro caso real), pero está roto para los demás formatos que la función dice soportar (DIVA GIS, GADM), con una inconsistencia interna adicional en la rama ADM2-GADM. | Minor-a-Mayor |
| 38 | **[Python, revisión de código]** `get_data_from_web()` (usada para WorldPop y geoBoundaries) sí valida `response.raise_for_status()`; `acquire_latest_osm_data()` (usada para OSM/Geofabrik, Amendment #21) no lo hace — inconsistencia interna dentro del propio código Python, no solo una diferencia con R. | Minor |
| 39 | **[Python, revisión de código]** Código muerto/confuso en `generate_folium_travel_map()`: un `.sort_values(ascending=True)` sobre una columna de población cuyo resultado se descarta al reasignarse (pandas realinea por índice) — sin efecto funcional real, pero confuso de leer. | Minor, cosmético |
| 40 | **[Python, revisión de código]** El patrón de leyenda log10 sin des-transformar (Amendment #17, visto en el dashboard) también aparece en los mapas HTML estáticos generados por `generate_folium_travel_map()` (`legend_name="Population estimates (log10)"`) — no es exclusivo del dashboard interactivo, es un patrón repetido en el código de visualización. | Minor (UX), refuerza #17 |

**Nota / hipótesis con evidencia de código para el hallazgo crítico #1 [Python, revisión de código]:** `process_healthsites_hcf_data()` no filtra ninguna facility por coordenadas faltantes (solo renombra columnas y descarta duplicados por `id`), a diferencia de R que sí filtra explícitamente (149 filas removidas). Hipótesis no confirmada: el CSV de HDX (usado por R) puede incluir filas con coordenadas vacías; el GeoJSON (usado por Python) probablemente solo exporta features con geometría ya válida — los dos formatos de descarga podrían no ser snapshots directamente equivalentes del mismo dataset de origen. Es la pista más concreta encontrada hasta ahora para que el Developer investigue la causa raíz del hallazgo #1.

**Nota [Python, revisión de código]:** `fix_quarto_static_assets.py` es un script de utilidad no documentado en ninguna guía que parchea manualmente assets estáticos generados por Quarto en el `app.py` del dashboard — sugiere que el Developer ya conocía fricciones en el proceso de build del dashboard (posiblemente relacionado con el Amendment #23 de `nbclient` faltante).

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | **No** | Hallazgo de paridad R/Python (Amendment #1) es un problema central de accuracy — los resultados no son consistentes entre implementaciones para el mismo input |
| Technical accuracy | **No** | Ídem — no se puede confiar en que ambas implementaciones den resultados técnicamente correctos y equivalentes |
| Prerequisite skills and knowledge | **No** | No se especifican requisitos de memoria/hardware (Amendment #26); tampoco se advierte la necesidad de cambiar de rama de git para el workflow subnacional (Amendment #4) |

### Structure and Organisation / Coherence / Accessibility

*(pendiente — no evaluado en detalle en esta sesión)*

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices (naming, logic, hardcoded values) | **Mayormente bueno** — nombres claros, manejo de errores robusto (reintentos, validación MD5). Ver nota de `find_crs()` como buena práctica embrionaria | **Partial** — hardcoded values no cumplido (Amendment #20); bug de precedencia de operadores en `clean_gdf_boundaries()` (Amendment #37); inconsistencia interna en validación de descargas (Amendment #38) | Revisión completada en ambos lenguajes |
| Code documentation (roxygen2/docstrings) | **Partial** — presente y detallado en general, pero con patrón confirmado de valores default desactualizados y un caso de copy-paste (Amendments #32-35) | **Partial** — import muerto sin comentario (Amendment #19); docstrings en general presentes y razonablemente completos en los archivos revisados | |
| Data management | ✅ Sin datos sensibles | ✅ Sin datos sensibles | |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** técnico (Malawi y San Juan corren exitosamente, con evidencia de tiempos y outputs) — ver hallazgo de paridad para matices de exactitud de resultados. ❌ **FAIL (esperado)** — Argentina nacional, con causa raíz precisa | ✅ **PASS** técnico (Malawi) — ídem matiz de paridad. ❌ **FAIL (esperado)** — Argentina nacional, causa raíz precisa | |
| Tested using alternative input data | ✅ Argentina (nacional + subnacional) probado además de Malawi | ✅ Argentina probado además de Malawi | Falta probar con fuente de datos distinta a healthsites.io en ambos lenguajes (ej. registro oficial Malawi MHFR en R) |
| Dependency management | ✅ Documentado correctamente; sin fricción mayor en instalación; buen manejo de descarga OSM (índice Geofabrik vs diccionario hardcodeado de Python) | **No cumplido** — `environment.yml` roto (Amendment #11), método alternativo incompleto (Amendment #23) | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Source code available, complies with QA checklist for code | *(pendiente)* | |
| README submitted, easy to follow | *(pendiente)* | |
| Interface clear and easy to understand | ✅ Confirmado visualmente en R (24/08, reconfirmado 01/09) y Python (25/08) — controles funcionan como documenta la Methodology | ⚠️ Mapa base de R no carga (Amendment #6). ⚠️ Botón de breakdown de Python no responde (Amendment #5) |
| Expected outputs clearly communicated | **No** | Ver hallazgo de paridad (Amendment #1) — los outputs no son consistentes entre implementaciones. Además: leyenda log10 confusa (Amendment #17); `FileNotFoundError` crudo ante datos faltantes (Amendment #24) |
| Sensitive input data omitted/replaced | ✅ No sensitive data included (confirmado también por el propio Developer en Acceptance Criteria) | |
| Input data available to download | *(pendiente)* | |
| End-to-end test by Tester | ✅ **PASS** — dashboard R verificado con Malawi (Central Region, 10 hospitales, 87% fuera de 8km, 8.208.511 personas, reconfirmado 01/09). ✅ **PASS** — dashboard Python verificado con Malawi (nacional, hospital, 10km, 82.7%, 24.117.974 personas) | |
| Tested with alternative input data | *(pendiente)* | |
| Compatible desktop/tablet/smartphone | **No testeado — aceptado por criterio ya declarado del Developer** (Acceptance Criteria recomienda uso en desktop explícitamente) | No requiere trabajo adicional |
| Runs independently of OS | ✅ Corrido en Windows sin problemas más allá de los workarounds de instalación ya documentados | |
| Memory/processing efficiency | ✅ Malawi (país chico) corrió rápido y sin errores de memoria en ambos lenguajes. ❌ **Argentina nacional — FAIL confirmado en ambos lenguajes** (límite de área del motor r5, 975.000 km²), con R tardando órdenes de magnitud más que Python en llegar al mismo resultado. ✅ **Argentina subnacional (San Juan) — PASS, muy eficiente** (red en 4.18s, accesibilidad en 1.69s) una vez usando la rama de git correcta | |

### Audio and video Products

N/A — la Unidad no incluye contenido audiovisual.

### Knowledge check / Quiz Products

*(pendiente confirmar si la Unidad incluye quiz)*

---

## Pedidos específicos del Developer (Acceptance Criteria — "Requests for additional testing criteria")

| Pedido | Estado |
| --- | --- |
| **R and Python**: testear ambos workflows usando las guías de usuario, reportar dificultades/bugs/errores | ✅ Hecho para ambos, con Malawi y Argentina. Hallazgo crítico de falta de paridad entre implementaciones (Amendment #1) |
| **Subnational run**: probar el workflow subnacional en Argentina para una provincia, evaluar si el approach es aceptable y si la documentación alcanza | ✅ **Hecho.** El approach en sí **es aceptable y funciona bien** una vez en la rama correcta (Amendment #4). La documentación (`03a-subnational-workflow.md`, marcada WIP) es técnicamente correcta en su contenido pero no advierte con suficiente claridad la necesidad de cambiar de rama de git, y omite el método correcto de filtrado de boundaries (Amendment #27). Nota: el Developer no especificó provincia; se usó San Juan por decisión y conveniencia del Tester, no Buenos Aires como en el ejemplo del Developer |
| **Main workflow**: correr el workflow principal para un país completo, notar dificultades | ✅ Hecho con Argentina en ambos lenguajes — **FAIL esperado y confirmado**, con evidencia técnica precisa en ambos casos (mismo límite de 975.000 km² del motor r5 subyacente) |

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio — relevante para justificar cronograma.
- No se encontró TdR de la Unidad; se trabaja asumiendo la idea original según documentación disponible.
- Malawi elegido como caso de control por ser el mismo que usó el Developer como prototipo — minimiza riesgo de que un fallo sea "por los datos" en vez de "por el código".
- El repositorio del Developer tiene al menos una rama activa (`r-subnational-workflow`) con funcionalidad relevante no mergeada a `main` y desactualizada respecto a ella — vale la pena preguntarle al Developer si hay más ramas en esta situación antes de dar por completo el testeo de código.
- Existe una carpeta `src/healthcare_accessibility/experimental/` con 10 archivos Python cuyo propósito no está claro — pregunta abierta para el Developer.
- Pendiente confirmar si existe el archivo `DESCRIPTION` (mencionado por la R User Guide) en `src/r/dashboard/`, un nivel arriba de la carpeta `R/` ya revisada.
- El hallazgo de paridad R/Python queda documentado con evidencia exacta pero sin causa raíz determinada — decisión consciente de alcance, dejada para que el Developer investigue en la próxima ronda.
- La revisión de código fuente en R reveló un patrón sistemático de docstrings desactualizados — mencionar como patrón único, no como hallazgos sueltos, en el reporte final.
- `find_crs()` en R (auto-selección de UTM por centroide) podría ser un punto de partida útil para que el Developer resuelva el problema de EPSG único en países grandes multi-faja.
- **Lección operativa:** en consolas tipo Anaconda Prompt/cmd y en Git Bash, pegar comandos mientras la consola espera una confirmación previa (`Proceed? y/n`) hace que los comandos se concatenen y se interpreten mal. Escribir/pegar un comando por vez y esperar el retorno del prompt evita el problema. Se observó el mismo síntoma de duplicación de texto en ambos tipos de consola.
- **Lección operativa:** en RGui/Windows, tras mucho tiempo con la ventana en segundo plano o bajo presión de memoria del sistema, la consola puede dejar de repintarse visualmente aunque el proceso siga vivo y trabajando — "Ventanas → Cascada" o redimensionar la ventana fuerza el repintado. Antes de asumir que un proceso está colgado, verificar actividad real en el Administrador de Tareas (CPU/disco), no solo la apariencia visual de la consola.
- **Lección operativa:** `git stash` + `git checkout <rama>` + `git stash pop` es un flujo seguro para cambiar de rama sin perder cambios de configuración locales no commiteados, aunque puede generar conflictos de merge en archivos modificados en ambas ramas (nuestro caso con ambos `config.yaml` y con `data_preparation.py`, en modo modify/delete).
