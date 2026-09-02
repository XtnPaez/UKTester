# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 01/09/2026 (noche)

---

## ⚠️ Corrección importante respecto a la versión anterior de este documento

La versión anterior de este documento afirmaba que el workflow nacional de R **"queda en estado de ejecución indefinida sin ningún mensaje de progreso o error"** al intentar el caso Argentina, calificándolo como un hallazgo Major distinto (y peor) que el de Python.

**Eso sigue siendo cierto para el caso *nacional* (país completo)**, pero se descubrió esta misma noche que el intento posterior de correr el caso **subnacional** (San Juan) tampoco había funcionado — no porque el approach subnacional esté roto, sino porque **está implementado en una rama de git separada (`r-subnational-workflow`) que nunca se mergeó a `main`**, y nosotros seguíamos ejecutando el script de `main`, que no lee `network_source_path` ni `analysis_mode`. Al cambiar a la rama correcta, el caso subnacional **corrió exitosamente en menos de 10 segundos** de cómputo pesado. Ver detalle completo más abajo.

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — falta revisión de código fuente en detalle y comparación de paridad R/Python)* |
| Reason for recommendation | *(pendiente)* |

## Testing Overview

- Tester: Cristian Páez (equipo Argentina).
- Documentación completa revisada antes de tocar código.
- Bloqueante de acceso al repositorio de código: sin acceso del 12/08 al 19/08 (una semana completa de la fase de testing).
- Entorno técnico R instalado y verificado en notebook sin permisos de administrador (R 4.4.0, Java 21 vía rJavaEnv, Quarto 1.9.38 portable).
- Pipeline R corrido end-to-end con datos reales, usando Malawi como caso de control. Dashboard R confirmado visualmente, reconfirmado 01/09.
- Entorno técnico Python resuelto vía Miniconda (modo "Just Me", sin admin).
- `data_preparation.py` y `pop_travel_times.py` (Python) corridos end-to-end con éxito con Malawi. Dashboard Python confirmado visualmente.
- **Sesión 01/09 — caso Argentina, workflow nacional (pedido explícito del Developer):**
  - Entorno Python reconstruido en la misma notebook, reproduciendo los bugs ya conocidos de `environment.yml` y `pyproject.toml` con evidencia de traceback completo.
  - Python `data_preparation.py`: exitoso para Argentina. `pop_travel_times.py`: **FAIL esperado y confirmado** — `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2`.
  - R `02_ttm.R` (workflow nacional, rama `main`): **3 intentos independientes**, todos detenidos indefinidamente en el mismo punto ("Attaching district names..."), sin fallar ni terminar durante horas (uno de ellos 4+ horas). Ninguno terminó por sí solo; requirió corte manual (uno vía suspensión accidental de la notebook, uno vía botón Stop, uno vía cierre forzado del proceso). **Se determinó luego que el proceso sí estaba avanzando, solo que muy lento** (descarga y construcción de red con el país completo de 428MB) — la apariencia de "colgado" en al menos un caso se debía a que la ventana de RGui había dejado de repintarse visualmente (resuelto con "Ventanas → Cascada"), no a un freeze real del proceso. Aun así, el intento nacional real terminó fallando con el mismo tipo de límite de área que Python: `Error in r5r::build_network(): Geographic extent of street layer exceeds limit of "975,000" km^2` — incluso cuando finalmente llegó a esa etapa, tardó órdenes de magnitud más que Python en llegar al mismo resultado.
- **Sesión 01/09 — caso Argentina, workflow subnacional (pedido explícito del Developer):**
  - Se identificó que el Developer provee un workflow subnacional específico para R en la rama de git `r-subnational-workflow` (mencionada en la Acceptance Criteria Template), con documentación dedicada en `docs/R/03a-subnational-workflow.md` (marcada como "WIP" por el propio Developer).
  - Se seleccionó San Juan como área de prueba (en vez de Buenos Aires, el ejemplo de la guía) por tener facilities de ejemplo ya confirmadas y evitar depender de fuentes de boundaries adicionales (GADM/Natural Earth).
  - Boundaries de San Juan (19 departamentos) filtradas correctamente por spatial join (centroide dentro del polígono provincial) contra el ADM2 de geoBoundaries — un filtro simple por nombre o por `st_intersects` produce resultados incorrectos (ver Amendments).
  - PBF recortado con `osmium-tool` (984 KB, contra 428 MB del país completo) usando el geojson de San Juan como polígono de recorte.
  - **Primer intento en R con la config subnacional armada dio el mismo error de límite de área que el caso nacional** — investigado, se determinó que el script `02_ttm.R` en la rama `main` (la que se estaba usando) **no lee `network_source_path` ni `analysis_mode` en absoluto**, ignorando por completo la configuración subnacional y descargando/usando siempre el país completo.
  - Se confirmó, comparando el código fuente de `02_ttm.R` entre `main` y `origin/r-subnational-workflow`, que la rama subnacional sí implementa la lógica correcta (`format_config()`, `validate_config()`, `define_area_name()`, uso condicional de `network_source_path`).
  - Se hizo checkout de la rama `r-subnational-workflow` (con `git stash` previo para no perder los cambios de configuración de Argentina hechos sobre `main`), resolviendo conflictos de merge en ambos `config.yaml` a favor de la configuración de Argentina/San Juan ya armada.
  - **Con el código correcto, el workflow subnacional para San Juan corrió exitosamente: red construida en 4.18s, accesibilidad calculada en 1.69s, outputs generados correctamente.** Confirmado el log `"Using provided network source file: data/network/san_juan/san_juan.osm.pbf"`.
  - **Hallazgo real resultante: no es que el approach subnacional esté mal diseñado — es que vive en una rama nunca mergeada a `main` y desactualizada respecto a ella** (le falta, por ejemplo, todo el árbol de código Python agregado posteriormente). Un usuario que siga la R User Guide principal sin conocer esta rama específica jamás la va a encontrar por su cuenta.
- Pendiente: revisión de código fuente en detalle (estilo, comentarios, documentación de funciones) en R y Python; comparación de paridad numérica R vs Python; decidir si el hallazgo de "R workflow nacional tarda órdenes de magnitud más que Python en llegar al mismo error" amerita ser reportado aparte.

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| El pipeline no crea automáticamente las carpetas de salida. Si no existen previamente, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o dar un mensaje claro. | Minor |
| La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real trae `X`, `Y` en mayúscula, confirmado con Malawi y Argentina. El código de limpieza (`rename_with(tolower)`) maneja esto correctamente de forma deliberada — es solo una imprecisión de la documentación. | Minor (documentación) |
| La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/500 en nuestra prueba. Se resolvió con geoBoundaries local (fallback ya contemplado por la guía), pero vale la pena advertir más explícitamente que la vía automática puede no ser confiable. | Minor |
| El campo `ownership` aparece como `NA` en el popup del dashboard para varias facilities — calidad de datos de la fuente healthsites.io, no bug de código. | Minor / nota |
| `environment.yml` usa la sintaxis `pip: - -r file:requirements.txt`, interpretada como ruta absoluta (`file:///requirements.txt`), falla con error 404. Reconfirmado 01/09 con traceback completo. Corrección: `- -r requirements.txt`. | Minor |
| `pyproject.toml` no declara `[project]` con nombre/versión/dependencias. `pip install -e .` instala un paquete vacío "UNKNOWN". Reconfirmado 01/09. En Windows además requirió el workaround `SETUPTOOLS_USE_DISTUTILS=stdlib` + `--no-build-isolation`, no documentado. | Minor — afecta el primer paso de instalación documentado |
| `data_processing_funcs.py:642` calcula áreas de superposición sin reproyectar a CRS proyectado primero — imprecisión metodológica real (no solo cosmética) en la asignación de celdas a distritos en zonas de borde. Reconfirmado con Argentina. | Minor |
| El pipeline Python exige columna `id` en facilities (a diferencia de R, donde es opcional); no está suficientemente aclarado en la documentación. | Minor |
| `pop_travel_times.py` emite `RuntimeWarning: Some destination points could not be snapped to the street network` sin cuantificar cuántos puntos — dificulta evaluar impacto real. Mismo patrón de ambigüedad se repite en R: `"No travel times returned for facility type 'dentist'"` en el caso subnacional de San Juan, sin distinguir si es porque no hay facilities de ese tipo en el área (normal) o porque existen pero no conectaron a la red (más preocupante). | Minor |
| Mismo patrón de imprecisión de CRS sin reproyectar, en `geospatial_utils.py:1580-1581`, al generar mapas de visualización. | Minor |
| El dashboard Python muestra en la leyenda de color valores crudos de escala log10 (ej. "3.9") en vez de población real — confuso para el usuario. | Minor (UX) |
| El mapa "National" del dashboard Python arranca con zoom muy alejado, mostrando países vecinos. | Minor / sugerencia UX |
| `data_preparation.py` importa `importlib_metadata` sin declararla como dependencia, para un objeto (`files`) que nunca se usa. | Minor |
| `health_data_source` está hardcodeado en `data_preparation.py` en vez de venir de config — contradice el criterio "Hardcoded values removed" marcado como "Yes" por el DP; debería ser **PARTIAL**. | Minor |
| `acquire_latest_osm_data()` no valida `response.status_code` antes de guardar el archivo descargado — un fallo de descarga se guarda silenciosamente como válido. | Minor |
| `process_healthsites_hcf_data()` no aplica fallback de `healthcare` → `facility_type` cuando `amenity` viene vacío, a diferencia de otra función del mismo repo que sí lo hace (`convert_hcf_polygons_to_points`). Evidencia real en geojson de Argentina (facility "Dharma"). | Minor |
| El método de instalación alternativo (plan B, usado cuando `environment.yml` falla) no instala `nbclient`/`jupyter`, requerido por Quarto para renderizar el dashboard Python. | Minor |
| **MAYOR:** `analysis_crs` (Python) asume un único EPSG proyectado por país — inadecuado para países grandes multi-faja como Argentina (sistema POSGAR 2007 dividido en 7 fajas oficialmente por esta misma razón). Se usó EPSG:32720 (UTM 20S) como aproximación práctica, no como solución real. La guía no ofrece ningún criterio para elegir `analysis_crs` en países grandes. | **Major** |
| El dashboard Python no maneja con gracia la ausencia del parquet de tiempos de viaje cuando el pipeline previo no completó — `FileNotFoundError` crudo en vez de mensaje claro. Confirmado con Argentina (nacional). | Minor |
| `data_preparation.py` no imprime confirmación de finalización exitosa — termina en silencio. Mismo patrón en R: `01_preprocess.R` tampoco imprime un mensaje final explícito de éxito. | Minor |
| La documentación (R y Python) no especifica requisitos de memoria/hardware según tamaño de país o dataset. | Minor |
| El dashboard R (Malawi) no carga el mapa base — placeholder "API KEY REQUIRED" de CARTO en vez de mapa de calles, sugiriendo una dependencia de API key no documentada. | Minor-a-Mayor |
| **MAYOR:** El workflow nacional en R (`02_ttm.R`, rama `main`) no tiene ningún chequeo temprano de extensión geográfica antes de intentar construir la red — a diferencia de Python, que falla en segundos con causa clara. Con Argentina completa, el proceso tardó del orden de horas en llegar al mismo error de límite de área (975,000 km²) que Python reporta casi instantáneamente. Esto no es "R se cuelga indefinidamente" (corrección de una nota anterior) — el proceso sí avanza y sí eventualmente falla con el mismo error, pero de forma extremadamente ineficiente comparado con Python, sin ningún indicador de progreso intermedio que permita al usuario estimar cuánto va a tardar o si vale la pena esperar. | **Major** |
| **MAYOR:** El workflow subnacional para R (`analysis_mode: subnational`, `network_source_path`, `subnational_area`), descrito en `docs/R/03a-subnational-workflow.md`, está implementado en la rama de git `r-subnational-workflow`, la cual **nunca fue mergeada a `main`** y está **desactualizada respecto a `main`** (le falta, por ejemplo, todo el árbol de código Python agregado posteriormente). La R User Guide principal no advierte en ningún lugar destacado que hace falta cambiar de rama completa para acceder a esta funcionalidad — solo se menciona de pasada en la Acceptance Criteria Template del propio Developer. Un usuario que siga únicamente la R User Guide nunca descubriría esta rama por sí solo. **Importante: una vez en la rama correcta, la funcionalidad subnacional en sí funciona correctamente y de forma eficiente** (ver PASS en Testing Overview) — el problema es puramente de organización/descubribilidad del repositorio, no de la lógica implementada. | **Major** (gestión de repositorio, no de funcionalidad) |
| El filtrado de boundaries a un área subnacional por nombre de texto (`grepl` contra `shapeName`) es insuficiente porque existen departamentos homónimos en distintas provincias argentinas (ej. "25 de Mayo", "9 de Julio" aparecen en varias provincias). Un filtro por `st_intersects` geométrico también es insuficiente porque incluye departamentos vecinos que solo tocan el borde. El método correcto (centroide dentro del polígono provincial) no está documentado en `03a-subnational-workflow.md`, que solo dice "filter to keep only municipalities within [área]" sin detallar cómo. | Minor |
| `01_preprocess.R`, al pasar de modo `country` a `subnational` reusando la misma carpeta de proyecto, sobrescribió el archivo `argentina_districts.geojson` del intento nacional anterior sin avisar (mismo nombre base). En la rama subnacional este problema no se repite (usa `<area>_districts.geojson`), pero es una nota sobre el comportamiento en `main`. | Minor / nota |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | Partial | Ver Amendment de `analysis_crs` — afecta precisión en países grandes |
| Technical accuracy | *(pendiente)* | |
| Prerequisite skills and knowledge | **No** | No se especifican requisitos de memoria/hardware; tampoco se advierte claramente la necesidad de cambiar de rama de git para el workflow subnacional |

### Structure and Organisation / Coherence / Accessibility

*(pendiente — no evaluado en detalle en esta sesión)*

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices (hardcoded values, naming, logic) | *(pendiente revisión formal)* | **Partial** — hardcoded values: No cumplido (`health_data_source`) | |
| Code documentation | *(pendiente)* | **Partial** — import muerto sin comentario | |
| Data management | ✅ Sin datos sensibles | ✅ Sin datos sensibles | |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** — Malawi (nacional) y San Juan (subnacional) ambos exitosos, con evidencia de tiempos y outputs. ❌ **FAIL (esperado)** — Argentina nacional, con causa raíz precisa (límite de área r5, confirmado también en R) | ✅ **PASS** (Malawi). ❌ **FAIL (esperado)** — Argentina nacional, causa raíz precisa (`IllegalArgumentException`, 975,000 km²) | |
| Tested using alternative input data | ✅ Argentina (nacional + subnacional) probado además de Malawi | ✅ Argentina probado además de Malawi | |
| Dependency management | ✅ Documentado correctamente, sin fricción mayor en instalación | **No cumplido** — `environment.yml` roto, método alternativo incompleto (falta `nbclient`) | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Interface clear and easy to understand | ✅ R y Python confirmados visualmente con Malawi | ⚠️ Hallazgo: mapa base de R no carga ("API KEY REQUIRED") |
| Expected outputs clearly communicated | ✅ Coincide con documentación | ⚠️ Leyenda log10 confusa (Python). ⚠️ `FileNotFoundError` crudo ante datos faltantes (Python) |
| Sensitive input data omitted/replaced | ✅ | |
| End-to-end test by Tester | ✅ **PASS** — dashboards R y Python verificados con Malawi | |
| Memory/processing efficiency | ✅ Malawi rápido en ambos. ❌ Argentina nacional — FAIL confirmado en ambos lenguajes (límite de área r5), con R tardando órdenes de magnitud más que Python en llegar al mismo resultado. ✅ **Argentina subnacional (San Juan) — PASS, muy eficiente** (red en 4.18s, accesibilidad en 1.69s) una vez usando la rama de git correcta | |

---

## Pedidos específicos del Developer (Acceptance Criteria — "Requests for additional testing criteria")

| Pedido | Estado |
| --- | --- |
| **R and Python**: testear ambos workflows, reportar dificultades/bugs | ✅ Hecho para ambos, con Malawi y Argentina |
| **Subnational run**: probar el workflow subnacional en Argentina, evaluar si el approach es aceptable y si la documentación alcanza | ✅ **Hecho.** El approach en sí **es aceptable y funciona bien** una vez en la rama correcta. La documentación del workflow subnacional (`03a-subnational-workflow.md`) es técnicamente correcta pero no advierte con suficiente claridad la necesidad de cambiar de rama de git — esto sí representa un problema real de usabilidad de la documentación, aunque no del método en sí |
| **Main workflow**: correr el workflow completo para un país, notar dificultades | ✅ Hecho con Argentina en ambos lenguajes — **FAIL esperado y confirmado**, con evidencia técnica precisa en ambos casos |

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio.
- No se encontró TdR de la Unidad.
- El repositorio del Developer tiene al menos una rama activa (`r-subnational-workflow`) con funcionalidad relevante no mergeada a `main` y desactualizada respecto a ella — vale la pena preguntarle al Developer si hay más ramas en esta situación antes de dar por completo el testeo de código.
- Lección operativa (01/09): en RGui/Windows, tras mucho tiempo con la ventana en segundo plano o bajo presión de memoria del sistema, la consola puede dejar de repintarse visualmente aunque el proceso siga vivo y trabajando — "Ventanas → Cascada" o redimensionar la ventana fuerza el repintado. Antes de asumir que un proceso está colgado, verificar actividad real en el Administrador de Tareas (CPU/disco), no solo la apariencia visual de la consola.
- Lección operativa (01/09): `git stash` + `git checkout <rama>` + `git stash pop` es un flujo seguro para cambiar de rama sin perder cambios de configuración locales no commiteados, aunque puede generar conflictos de merge en archivos modificados en ambas ramas (nuestro caso con ambos `config.yaml`).
