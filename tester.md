# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 01/09/2026 (noche, tarde)

---

## ⚠️ Hallazgo más importante de toda la sesión — leer primero

**R y Python no son funcionalmente equivalentes para el mismo país y el mismo tipo de fuente de datos.** Comparando el conteo de facilities procesadas para Malawi (mismo origen: healthsites.io):

| Tipo | R | Python | Diferencia |
| --- | --- | --- | --- |
| clinic | 48 | 67 | -19 (-28%) |
| dentist | 6 | 8 | -2 |
| doctors | 1 | 2 | -1 |
| hospital | 71 | 195 | **-124 (-64%)** |
| pharmacy | 26 | 27 | -1 |
| **Total** | **152** | **299** | **-147 (-49%)** |

Python procesa prácticamente **el doble** de facilities que R para el mismo país. Esto se refleja en cascada en los resultados de accesibilidad mostrados al usuario final (mismo filtro exacto — Nacional, clinic, 10km, Total population):

| | R | Python |
| --- | --- | --- |
| % población fuera de rango | 84.1% | 76.1% |
| Población estimada más allá | 18.423.545 | 22.187.103 |

**Causa raíz: no determinada.** Se descartó que la diferencia de mayúsculas/minúsculas en columnas (`X`/`Y` vs `x`/`y`) sea la causa, ya que el código R la maneja correctamente. La cifra de "149 filas removidas por falta de coordenadas" (warning de R) es demasiado pequeña para explicar una diferencia de 147 facilities totales. Hipótesis no verificadas: los dos pipelines pudieron descargar snapshots distintos de healthsites.io/HDX en fechas distintas (R usa CSV, Python usa GeoJSON, descargados en sesiones separadas); o hay algún filtro adicional (ej. campo `completeness`, `operational_status`) aplicado por un lenguaje y no por el otro.

**Decisión de alcance:** se documenta este hallazgo con evidencia numérica exacta y reproducible, y se deja la investigación de causa raíz para que el Developer la resuelva en la próxima ronda — determinar por qué dos pipelines que leen la misma fuente llegan a conteos tan distintos requiere acceso al contexto interno del desarrollo que excede el alcance razonable de este ciclo de testing.

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — el hallazgo de paridad R/Python arriba es candidato fuerte a definir esto como Rejected — major amendments)* |
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
  - Python `data_preparation.py`: exitoso para Argentina. `pop_travel_times.py`: **FAIL esperado y confirmado** — `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2`.
  - R `02_ttm.R` (workflow nacional, rama `main`): tras varios intentos con apariencia de "colgado" (resultó ser solo una ventana de RGui sin repintar, no un freeze real), terminó fallando con el mismo tipo de límite de área que Python (`Geographic extent of street layer exceeds limit of "975,000" km^2`), pero tardando órdenes de magnitud más en llegar a ese resultado, sin ningún chequeo temprano ni indicador de progreso.
- **Sesión 01/09 — caso Argentina, workflow subnacional (pedido explícito del Developer):**
  - Identificado que la funcionalidad subnacional para R vive en la rama de git `r-subnational-workflow` (mencionada solo de pasada en la Acceptance Criteria Template), no mergeada a `main` y desactualizada respecto a ella (le falta, por ejemplo, todo el árbol de código Python agregado después).
  - Tras cambiar a la rama correcta (con `git stash` para preservar la configuración de Argentina), el workflow subnacional para San Juan **corrió exitosamente en menos de 10 segundos** de cómputo pesado, usando un PBF recortado con `osmium-tool` (984 KB vs 428 MB del país completo).
  - Conclusión: el approach subnacional en sí **es aceptable y funciona bien**; el problema real es de organización/descubribilidad del repositorio (rama sin mergear), no de la lógica implementada.
- **Sesión 01/09 (noche) — comparación de paridad R vs Python con Malawi:**
  - Se configuraron ambos dashboards con exactamente el mismo filtro (Nacional, clinic, 10km, Total population) para una comparación justa.
  - **Hallazgo mayor descripto arriba**: diferencia de ~49% en el conteo total de facilities procesadas entre R y Python para el mismo país y tipo de fuente.
  - Hallazgo adicional: el botón "Show health facility breakdown" del dashboard Python no responde a clicks — sin error en consola de navegador ni en el servidor, sugiriendo un callback no conectado.
  - Hallazgo adicional: recargar la página del dashboard Python (F5/Ctrl+F5) resetea los filtros del usuario al valor por defecto en vez de mantener la sesión.
  - Hallazgo adicional: `www/whiteAAlogo.png` retorna 404 en el dashboard Python — asset faltante.
- Pendiente: revisión de código fuente en detalle (estilo, comentarios, documentación de funciones) en R y Python; investigación de causa raíz de la discrepancia de facilities (dejada para el Developer, ver nota de alcance arriba).

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| **CRÍTICO/MAYOR: R y Python procesan un número de facilities radicalmente distinto para el mismo país (Malawi) y el mismo tipo de fuente (healthsites.io): 152 vs 299 facilities totales (~49% de diferencia), con hospital siendo la categoría más afectada (71 vs 195, -64%). Esto se propaga a los resultados de accesibilidad mostrados al usuario (84.1% vs 76.1% de población fuera de rango; 18.4M vs 22.2M personas estimadas). Causa raíz no determinada — requiere investigación del Developer.** | **Major (crítico)** |
| El botón "Show health facility breakdown" del dashboard Python no responde a clicks — no se observó error en consola de navegador ni actividad nueva en el log del servidor al presionarlo. | Minor-a-Mayor |
| Recargar la página del dashboard Python resetea los filtros del usuario a los valores por defecto en vez de preservar la sesión/selección. | Minor |
| Asset faltante: `www/whiteAAlogo.png` retorna 404 repetidamente en el dashboard Python. | Minor |
| El pipeline no crea automáticamente las carpetas de salida. Si no existen previamente, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o dar un mensaje claro. | Minor |
| La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real trae `X`, `Y` en mayúscula, confirmado con Malawi y Argentina. El código de limpieza (`rename_with(tolower)`) maneja esto correctamente de forma deliberada — es solo una imprecisión de la documentación. | Minor (documentación) |
| La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/500 en nuestra prueba. Se resolvió con geoBoundaries local (fallback ya contemplado por la guía). | Minor |
| El campo `ownership` aparece como `NA` en el popup del dashboard para varias facilities — calidad de datos de la fuente, no bug de código. | Minor / nota |
| `environment.yml` usa la sintaxis `pip: - -r file:requirements.txt`, interpretada como ruta absoluta, falla con error 404. Reconfirmado 01/09. Corrección: `- -r requirements.txt`. | Minor |
| `pyproject.toml` no declara `[project]`. `pip install -e .` instala un paquete vacío "UNKNOWN". Reconfirmado 01/09. Requirió workaround `SETUPTOOLS_USE_DISTUTILS=stdlib` + `--no-build-isolation` en Windows, no documentado. | Minor |
| `data_processing_funcs.py:642` calcula áreas de superposición sin reproyectar a CRS proyectado primero — imprecisión metodológica real. Reconfirmado con Argentina. | Minor |
| El pipeline Python exige columna `id` en facilities (a diferencia de R, donde es opcional); no está suficientemente aclarado en la documentación. | Minor |
| `pop_travel_times.py` y R ambos emiten warnings de puntos/tipos sin cobertura sin cuantificar el impacto (`"Some destination points could not be snapped"` en Python; `"No travel times returned for facility type 'dentist'"` en R). | Minor |
| Mismo patrón de imprecisión de CRS sin reproyectar en `geospatial_utils.py:1580-1581`. | Minor |
| El dashboard Python muestra en la leyenda de color valores crudos de escala log10 en vez de población real — confuso para el usuario. | Minor (UX) |
| El mapa "National" del dashboard Python arranca con zoom muy alejado, mostrando países vecinos. | Minor / sugerencia UX |
| `data_preparation.py` importa `importlib_metadata` sin declararla como dependencia, para un objeto que nunca se usa. | Minor |
| `health_data_source` está hardcodeado en `data_preparation.py` en vez de venir de config — contradice el criterio "Hardcoded values removed" marcado como "Yes" por el DP; debería ser **PARTIAL**. | Minor |
| `acquire_latest_osm_data()` no valida `response.status_code` antes de guardar el archivo descargado. | Minor |
| `process_healthsites_hcf_data()` no aplica fallback de `healthcare` → `facility_type` cuando `amenity` viene vacío, a diferencia de otra función del mismo repo que sí lo hace. | Minor |
| El método de instalación alternativo (plan B) no instala `nbclient`/`jupyter`, requerido por Quarto para renderizar el dashboard Python. | Minor |
| **MAYOR:** `analysis_crs` (Python) asume un único EPSG proyectado por país — inadecuado para países grandes multi-faja como Argentina. Se usó EPSG:32720 (UTM 20S) como aproximación práctica. | **Major** |
| El dashboard Python no maneja con gracia la ausencia del parquet de tiempos de viaje — `FileNotFoundError` crudo. Confirmado con Argentina. | Minor |
| `data_preparation.py` y `01_preprocess.R` no imprimen confirmación explícita de finalización exitosa. | Minor |
| La documentación (R y Python) no especifica requisitos de memoria/hardware según tamaño de país o dataset. | Minor |
| El dashboard R (Malawi) no carga el mapa base — placeholder "API KEY REQUIRED" de CARTO. | Minor-a-Mayor |
| **MAYOR:** El workflow nacional en R no tiene chequeo temprano de extensión geográfica — tarda órdenes de magnitud más que Python en llegar al mismo error de límite de área (975,000 km²), sin indicadores de progreso. | **Major** |
| **MAYOR (gestión de repo, no de funcionalidad):** El workflow subnacional para R vive en la rama `r-subnational-workflow`, nunca mergeada a `main` y desactualizada respecto a ella. Una vez en la rama correcta, la funcionalidad **funciona bien y de forma eficiente**. | **Major** |
| El filtrado de boundaries a un área subnacional por nombre de texto es insuficiente (departamentos homónimos entre provincias argentinas); el método correcto (centroide dentro del polígono) no está documentado. | Minor |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | **No** | El hallazgo de paridad R/Python (arriba) es un problema de accuracy central — los resultados no son consistentes entre implementaciones para el mismo input |
| Technical accuracy | **No** | Ídem — no se puede confiar en que ambas implementaciones den resultados técnicamente correctos y equivalentes |
| Prerequisite skills and knowledge | **No** | No se especifican requisitos de memoria/hardware; tampoco se advierte la necesidad de cambiar de rama de git para el workflow subnacional |

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices | *(pendiente revisión formal)* | **Partial** — hardcoded values: No cumplido | |
| Code documentation | *(pendiente)* | **Partial** — import muerto sin comentario | |
| Data management | ✅ Sin datos sensibles | ✅ Sin datos sensibles | |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** técnico (corre) — pero ver hallazgo de paridad para matices sobre exactitud de resultados | ✅ **PASS** técnico (corre) — ídem | |
| Tested using alternative input data | ✅ Argentina (nacional + subnacional) probado además de Malawi | ✅ Argentina probado además de Malawi | |
| Dependency management | ✅ Sin fricción mayor | **No cumplido** — `environment.yml` roto, método alternativo incompleto | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Interface clear and easy to understand | ✅ R y Python confirmados visualmente con Malawi | ⚠️ Mapa base de R no carga; botón de breakdown de Python no responde |
| Expected outputs clearly communicated | **No** | Ver hallazgo de paridad — los outputs no son consistentes entre implementaciones |
| Sensitive input data omitted/replaced | ✅ | |
| End-to-end test by Tester | ✅ Técnicamente sí, con matices de exactitud | |
| Memory/processing efficiency | ✅ Malawi rápido en ambos. ❌ Argentina nacional FAIL confirmado (ambos). ✅ Argentina subnacional PASS (San Juan, rama correcta) | |

---

## Pedidos específicos del Developer (Acceptance Criteria — "Requests for additional testing criteria")

| Pedido | Estado |
| --- | --- |
| **R and Python**: testear ambos workflows, reportar dificultades/bugs | ✅ Hecho — con el hallazgo crítico de falta de paridad entre ambos |
| **Subnational run**: probar el workflow subnacional en Argentina, evaluar si el approach es aceptable y si la documentación alcanza | ✅ Hecho. El approach **es aceptable y funciona bien** una vez en la rama correcta; la documentación no advierte con claridad la necesidad de cambiar de rama |
| **Main workflow**: correr el workflow completo para un país, notar dificultades | ✅ Hecho — FAIL esperado y confirmado en ambos lenguajes, con evidencia técnica precisa |

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio.
- No se encontró TdR de la Unidad.
- El repositorio tiene al menos una rama (`r-subnational-workflow`) con funcionalidad relevante no mergeada a `main` y desactualizada — vale la pena preguntarle al Developer si hay más ramas en esta situación.
- **El hallazgo de paridad R/Python queda documentado con evidencia exacta pero sin causa raíz determinada — decisión consciente de alcance, dejada para que el Developer investigue en la próxima ronda de desarrollo.**
- Lección operativa: en RGui/Windows, la consola puede dejar de repintarse visualmente bajo presión de memoria del sistema, aunque el proceso siga vivo — verificar actividad real en el Administrador de Tareas antes de asumir que algo está colgado.
- Lección operativa: `git stash` + `git checkout <rama>` + `git stash pop` es un flujo seguro para cambiar de rama sin perder cambios locales no commiteados.
