# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 02/09/2026

---

## ⚠️ Hallazgo más importante de toda la sesión — leer primero

**R y Python no son funcionalmente equivalentes.** Comparando el conteo de facilities procesadas para Malawi (mismo origen: healthsites.io):

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

**Causa raíz: no determinada.** Documentado con evidencia numérica exacta y reproducible; se deja para que el Developer la investigue en la próxima ronda.

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — el hallazgo de paridad R/Python es candidato fuerte a definir esto como Rejected — major amendments)* |
| Reason for recommendation | *(pendiente)* |

## Testing Overview

- Tester: Cristian Páez (equipo Argentina).
- Bloqueante de acceso al repositorio de código: sin acceso del 12/08 al 19/08.
- Entornos técnicos R y Python instalados y verificados, sin permisos de administrador.
- Pipelines R y Python corridos end-to-end con Malawi (caso de control del Developer) — ambos dashboards confirmados visualmente.
- **Caso Argentina (país grande, pedido explícito del Developer):**
  - Workflow nacional: **FAIL esperado y confirmado en ambos lenguajes** — Python falla en segundos (`IllegalArgumentException`, límite de área de 975,000 km²); R llega al mismo tipo de error pero tarda órdenes de magnitud más, sin chequeo temprano.
  - Workflow subnacional (San Juan, elegido por el Tester — el Developer no especifica provincia, su propio ejemplo usa Buenos Aires): **PASS**, tras descubrir que la funcionalidad vive en la rama de git `r-subnational-workflow`, nunca mergeada a `main` y desactualizada respecto a ella.
- **Comparación de paridad R vs Python con Malawi: hallazgo crítico** de discrepancia de ~49% en facilities procesadas (ver arriba).
- **Sesión 02/09 — revisión de código fuente en R (11 archivos de `src/r/dashboard/R/`):** ver sección de Amendments actualizada abajo. Calidad general buena (manejo de errores robusto, roxygen2 presente), con algunos hallazgos de documentación desactualizada y una asimetría interesante a favor de R en el manejo de descargas de OSM.
- Pendiente: revisión de código fuente en Python; investigación de causa raíz de la discrepancia de facilities (dejada para el Developer).

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| **CRÍTICO/MAYOR: R y Python procesan un número de facilities radicalmente distinto para el mismo país (Malawi) y el mismo tipo de fuente: 152 vs 299 facilities totales (~49% de diferencia), con hospital como categoría más afectada (71 vs 195, -64%). Se propaga a los resultados de accesibilidad mostrados al usuario. Causa raíz no determinada.** | **Major (crítico)** |
| El botón "Show health facility breakdown" del dashboard Python no responde a clicks. | Minor-a-Mayor |
| Recargar la página del dashboard Python resetea los filtros del usuario a los valores por defecto. | Minor |
| Asset faltante: `www/whiteAAlogo.png` retorna 404 en el dashboard Python. | Minor |
| **[R, 02/09] Causa raíz confirmada del bug de mapa base**: `dashboard_map.R` llama a `leaflet::addProviderTiles("CartoDB.Positron")` sin API key configurada — CARTO ahora la exige para ese proveedor. | Minor (ya conocido, ahora con causa exacta) |
| **[R, 02/09]** Docstring desactualizado: `compute_closest_accessibility()` documenta `max_travel_time` con default 120 minutos en el roxygen2, pero el valor real del parámetro en el código es 167 (coincide con lo que sí dice la R User Guide externa — es la documentación *interna* la que quedó vieja). | Minor |
| **[R, 02/09]** Mismo patrón: `get_osm_districts()` documenta `timeout_seconds` default 120 en el roxygen2, el código real usa 300. | Minor |
| **[R, 02/09]** Copy-paste de documentación: el docstring de `download_worldpop()` es una copia literal del de `get_subgroup_population_files()` (describe extracción de zip y revisión de carpetas), pero `download_worldpop()` solo descarga el archivo. | Minor |
| **[R, 02/09] Patrón general:** los tres hallazgos anteriores sugieren que cuando se cambian valores por defecto en el código, no se actualiza la documentación roxygen2 correspondiente — no son errores aislados, es un patrón sistemático de mantenimiento de documentación. | Minor (patrón) |
| **[R, 02/09] Nota positiva / recomendación cruzada:** `download_geofabrik_pbf()` en R resuelve URLs de país consultando el índice JSON en vivo de Geofabrik, evitando el problema de diccionario hardcodeado que causó el bug de Python ("south-america" vs "south_america" para Argentina). Se recomienda que Python adopte un enfoque similar en lugar de mantener `country_continent_dict` a mano. | Nota / recomendación |
| **[R, 02/09] Nota:** `add_district_to_points.R` incluye una función `find_crs()` que auto-selecciona una proyección UTM según el centroide del país — un enfoque embrionario al mismo problema del hallazgo Mayor de CRS único en Python. Solo se usa para el método de asignación `raster`, no para el cálculo de travel-time en sí, pero podría ser un punto de partida para que el Developer resuelva el problema de EPSG único en países multi-faja. | Nota / posible pista de solución |
| El pipeline no crea automáticamente las carpetas de salida en algunos casos (`01_preprocess.R`). | Minor |
| La R User Guide documenta columnas `x`, `y`, `osm_id` en minúscula; el archivo real trae mayúscula. El código (`rename_with(tolower)`) lo maneja correctamente — es solo imprecisión de documentación. | Minor (documentación) |
| La descarga automática de boundaries desde Overpass API falló por timeout/500 en nuestra prueba; resuelto con geoBoundaries local. | Minor |
| `environment.yml` con bug de sintaxis (`file:requirements.txt`), reconfirmado. | Minor |
| `pyproject.toml` sin `[project]`, instala paquete como "UNKNOWN", reconfirmado. Requiere workaround en Windows no documentado. | Minor |
| `data_processing_funcs.py:642` calcula áreas sin reproyectar a CRS proyectado — imprecisión metodológica real. | Minor |
| Columna `id` obligatoria en Python (opcional en R) no aclarada en documentación. | Minor |
| Warnings sin cuantificar en ambos lenguajes (puntos sin conectar en Python; facility type sin cobertura en R). | Minor |
| Imprecisión de CRS repetida en `geospatial_utils.py`. | Minor |
| Leyenda log10 confusa en dashboard Python. | Minor (UX) |
| Zoom inicial alejado en mapa "National" de Python. | Minor / UX |
| `importlib_metadata` no declarada como dependencia en Python, para un import muerto. | Minor |
| `health_data_source` hardcodeado en Python — contradice "Hardcoded values removed" declarado como cumplido por el DP. | Minor |
| `acquire_latest_osm_data()` en Python no valida `response.status_code`. | Minor |
| `process_healthsites_hcf_data()` sin fallback `healthcare`→`facility_type` en Python. | Minor |
| Método de instalación alternativo en Python no instala `nbclient`/`jupyter`. | Minor |
| **MAYOR:** `analysis_crs` (Python) asume un único EPSG por país — inadecuado para países multi-faja como Argentina. | **Major** |
| Dashboard Python no maneja con gracia datos faltantes (`FileNotFoundError` crudo). | Minor |
| `data_preparation.py` y `01_preprocess.R` no confirman finalización exitosa. | Minor |
| Documentación no especifica requisitos de memoria/hardware según tamaño de país. | Minor |
| **MAYOR:** workflow nacional de R sin chequeo temprano de extensión geográfica — tarda órdenes de magnitud más que Python en llegar al mismo error. | **Major** |
| **MAYOR (gestión de repo):** workflow subnacional de R en rama nunca mergeada a `main`. Funciona bien una vez ahí. | **Major** |
| Filtrado de boundaries subnacional por nombre de texto es insuficiente (departamentos homónimos entre provincias). | Minor |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Accuracy | **No** | Hallazgo de paridad R/Python — problema central de accuracy |
| Technical accuracy | **No** | Ídem |
| Prerequisite skills and knowledge | **No** | Falta info de memoria/hardware y de necesidad de cambiar de rama de git |

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices (naming, logic, hardcoded values) | **Mayormente bueno** — nombres claros, manejo de errores robusto (reintentos, validación MD5). Ver nota de `find_crs()` como buena práctica embrionaria | **Partial** — hardcoded values no cumplido | Revisión Python pendiente completar |
| Code documentation (roxygen2/docstrings) | **Partial** — presente y detallado en general, pero con 2 casos confirmados de valores default desactualizados y 1 caso de copy-paste incorrecto (ver Amendments) | **Partial** — import muerto sin comentario | Patrón de docstrings desactualizados vale mención aparte en el reporte |
| Data management | ✅ Sin datos sensibles | ✅ Sin datos sensibles | |
| Tested end-to-end by Tester | ✅ PASS técnico — ver hallazgo de paridad para matices de exactitud | ✅ PASS técnico — ídem | |
| Dependency management | ✅ Sin fricción mayor en instalación; buen manejo de descarga OSM (índice Geofabrik vs diccionario hardcodeado de Python) | **No cumplido** — `environment.yml` roto | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Interface clear and easy to understand | ✅ Ambos confirmados con Malawi | ⚠️ Mapa base de R no carga (causa confirmada: falta API key de CARTO); botón de breakdown de Python no responde |
| Expected outputs clearly communicated | **No** | Ver hallazgo de paridad |
| Memory/processing efficiency | ✅ Malawi rápido en ambos. ❌ Argentina nacional FAIL confirmado (ambos). ✅ Argentina subnacional PASS (San Juan, rama correcta) | |

---

## Pedidos específicos del Developer (Acceptance Criteria)

| Pedido | Estado |
| --- | --- |
| **R and Python**: testear ambos, reportar dificultades | ✅ Hecho — con hallazgo crítico de falta de paridad |
| **Subnational run**: Argentina, evaluar approach y documentación | ✅ Hecho. Approach aceptable y funcional una vez en la rama correcta; documentación no advierte la necesidad de cambiar de rama. Nota: el Developer no especificó provincia (su ejemplo usa Buenos Aires); se usó San Juan por conveniencia práctica del Tester |
| **Main workflow**: país completo, notar dificultades | ✅ Hecho — FAIL esperado y confirmado en ambos lenguajes |

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) por acceso al repositorio.
- No se encontró TdR de la Unidad.
- Rama `r-subnational-workflow` no mergeada a `main` y desactualizada — preguntar al Developer si hay más ramas en esta situación.
- El hallazgo de paridad R/Python queda documentado con evidencia exacta pero sin causa raíz determinada — decisión consciente de alcance.
- La revisión de código fuente en R reveló un patrón sistemático de docstrings desactualizados (roxygen2 no se actualiza cuando cambian los valores por defecto del código) — mencionar como patrón, no como 3 hallazgos sueltos.
- `find_crs()` en R (auto-selección de UTM por centroide) podría ser un punto de partida útil para que el Developer resuelva el problema de EPSG único en países grandes multi-faja (hallazgo Mayor de Python).
