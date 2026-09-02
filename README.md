# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

> **Nota de reconciliación (02/09/2026):** este README fue reconstruido revisando toda la sesión de testeo de punta a punta, para no perder notas de versiones anteriores. Ver `tester.md` para el detalle completo con evidencia; este archivo es el resumen ejecutivo.
>
> **Actualización 02/09/2026 (tarde):** revisión de código fuente en Python completada. Encontrado un bug real de precedencia de operadores en `clean_gdf_boundaries()`, y una pista de código concreta (aunque no confirmada) para la causa raíz del hallazgo crítico de paridad R/Python.

## ⚠️ Hallazgo crítico de la sesión

**R y Python no son funcionalmente equivalentes.** Para el mismo país (Malawi) y el mismo tipo de fuente de datos (healthsites.io), con configuración idéntica de dashboard, procesan un número de facilities radicalmente distinto:

- **Total: 152 (R) vs 299 (Python) — ~49% de diferencia**
- Hospital: 71 (R) vs 195 (Python) — la categoría más afectada
- Se propaga a los resultados mostrados al usuario: 84.1% vs 76.1% de población fuera de rango; 18.4M vs 22.2M personas estimadas más allá del umbral

**Causa raíz no determinada** — documentado con evidencia numérica exacta y reproducible; se deja para que el Developer investigue en la próxima ronda. Ver detalle completo en `tester.md`.

## Checkpoint actual

**Estamos en el paso 4a** (Tester testea el contenido) del proceso oficial. **Workflow R validado 100% end-to-end con Malawi, reconfirmado 01/09.** **Workflow Python validado 100% end-to-end con Malawi.** **Caso Argentina (pedidos explícitos del Developer) completo:**
- Workflow nacional: **FAIL esperado y confirmado en ambos lenguajes** (mismo límite de área del motor r5 subyacente, 975.000 km²), con R tardando órdenes de magnitud más que Python en llegar al mismo resultado.
- Workflow subnacional (San Juan, elección del Tester — el Developer no especifica provincia): **PASS**, tras descubrir que la funcionalidad de R vive en una rama de git separada (`r-subnational-workflow`) no mergeada a `main`.

**Revisión de código fuente completada en R (11 archivos) y en Python (7 archivos principales).** Falta: reunión con la NSO.

**Próximo hito real:** completar pasos 4a–4c y subir el Testing Recommendation Template — **deadline oficial: 4 de septiembre de 2026.**

*(Nota interna, no oficial: UK ofreció una extensión de plazo individual por el problema de acceso al repositorio, que se decidió no tomar formalmente en un primer momento; posteriormente se está negociando con UK una extensión hasta el miércoles 9 de septiembre.)*

| Paso oficial (Content Testing Quick Guide) | Estado |
| --- | --- |
| 1. Developer sube Unidad + Acceptance Criteria | ✅ Hecho (lado Developer) |
| 2. UK team revisa Acceptance Criteria | ✅ Hecho |
| 3. UK team flaggea la Unidad al Tester | ✅ Hecho (7/08) |
| **4a. Tester testea el contenido** | 🔄 **En curso, muy avanzado** |
| 4b. Tester + NSO acuerdan recomendación | ⏳ No iniciado |
| 4c. Tester completa Testing Recommendation Template | ⏳ No iniciado |
| 5. Tester sube el Template | ⏳ Deadline oficial: 4/09/2026 (posible extensión a 9/09) |
| 6. UK team flaggea al Developer | — Futuro |
| 7. Moderation Panel (si rechazo) | — Futuro, condicional |
| 8. Sign-off en Project Board | — Futuro |

## Qué tenemos

- Los 6 documentos de referencia del Developer, más `docs/R/03a-subnational-workflow.md` (marcado "WIP" por el Developer) de la rama `r-subnational-workflow`.
- Acceso completo y confirmado al repositorio de código (clonado exitoso, 20/08, tras una semana de bloqueo por proceso SyOps pendiente).
- Entorno técnico R completo y verificado, instalado sin permisos de administrador: R 4.4.0, Java 21 (vía rJavaEnv), Quarto 1.9.38 (portable). Reconfirmado sano el 01/09.
- **Pipeline R validado end-to-end con datos reales (caso Malawi, 24/08, reconfirmado 01/09):**
  - `01_preprocess.R`: boundaries (geoBoundaries ADM1), facilities (healthsites.io, 149 filas sin coordenadas descartadas — esperado), 6 rasters demográficos de WorldPop + stack combinado.
  - `02_ttm.R`: red construida en 66.57s, matriz de tiempo de viaje en 28.1s. Outputs `.csv` (~95MB) y `.parquet` (~13MB).
- **Dashboard R confirmado visualmente (24/08, reconfirmado 01/09):** Central Region, 10 hospitales, 87% de población fuera de 8km, 8.208.511 personas beyond, popups funcionando. Campo `ownership` como `NA` para varias facilities (calidad de fuente, no bug).
- **Entorno técnico Python completo y verificado (25/08):** Miniconda modo "Just Me", sin admin (pivote desde venv+pip por `cykhash` sin wheel de Windows en PyPI).
- **`data_preparation.py` y `pop_travel_times.py` validados end-to-end (Malawi, 25/08):** exit code 0 ambos, 75.64s cálculo de tiempos.
- **Dashboard Python confirmado visualmente (25/08):** nacional, hospital, 10km: 82.7% fuera de rango, 24.117.974 personas beyond.
- **Sesión 01/09 — caso Argentina completo (país grande, pedidos explícitos del Developer):**
  - Workflow nacional: Python falla en segundos (`IllegalArgumentException: Geographic extent of street layer exceeds limit of 975000 km2`); R llega al mismo tipo de error y mismo límite exacto tras órdenes de magnitud más de tiempo, sin chequeo temprano ni indicadores de progreso — investigado a fondo tras varios intentos que parecían "colgados" (resultó ser ventana de RGui sin repintar bajo presión de memoria, no un freeze real).
  - Workflow subnacional (San Juan — elección del Tester, no del Developer, cuyo ejemplo usa Buenos Aires): **PASS**, tras descubrir que la funcionalidad vive en la rama `r-subnational-workflow`, nunca mergeada a `main` y desactualizada respecto a ella (falta código Python agregado después). Una vez en la rama correcta: red construida en 4.18s, accesibilidad en 1.69s.
  - **Hallazgo mayor de EPSG único** para países multi-faja (`analysis_crs` en Python) — resuelto con aproximación práctica (EPSG:32720) para continuar el testeo.
- **Sesión 01/09 (noche) — comparación de paridad R vs Python con Malawi: hallazgo crítico** de discrepancia de ~49% en facilities procesadas — ver arriba y `tester.md` para el detalle completo, incluyendo cómo se obtuvo el dato (directamente por código, no por UI, ya que el botón de desglose del dashboard Python resultó estar roto).
- **Sesión 02/09 — revisión de código fuente en R completada** (11 archivos, `src/r/dashboard/R/`): calidad general buena; causa raíz confirmada del bug de mapa base; patrón sistemático de docstrings desactualizados; hallazgo positivo de R sobre manejo de descargas OSM; función embrionaria de auto-CRS que podría orientar la solución al hallazgo de EPSG único.
- **Sesión 02/09 (tarde) — revisión de código fuente en Python completada** (`data_processing_funcs.py`, `geospatial_utils.py`, `postprocessing.py`, `pop_travel_times.py`, `utils.py`, `accessability_metrics.py`, `fix_quarto_static_assets.py`): encontrado un **bug real de precedencia de operadores** en `clean_gdf_boundaries()` (funciona por casualidad con geoBoundaries, roto para otros formatos que dice soportar); una **hipótesis concreta con evidencia de código** para la causa raíz del hallazgo crítico de paridad (Python no filtra facilities sin coordenadas, a diferencia de R — podría deberse a que CSV vs GeoJSON de HDX no son snapshots equivalentes); una inconsistencia interna en Python sobre validación de descargas HTTP; y confirmación de que el patrón de leyenda log10 confusa se repite también en los mapas HTML estáticos, no solo en el dashboard.

## Hallazgos para Proposed Amendments (Testing Recommendation Template)

Ver el listado completo y numerado, con evidencia y clasificación Major/Minor, en `tester.md` (36 amendments + 2 notas positivas/recomendaciones cruzadas). Los de mayor peso:

- **CRÍTICO/MAYOR:** discrepancia de ~49% en facilities procesadas entre R y Python para el mismo país.
- **Mayor:** `analysis_crs` (Python) no soporta países grandes multi-faja como Argentina.
- **Mayor:** el workflow nacional de R no tiene chequeo temprano de extensión geográfica — tarda órdenes de magnitud más que Python en llegar al mismo error.
- **Mayor (gestión de repo, no de funcionalidad):** el workflow subnacional de R vive en una rama nunca mergeada a `main`. Una vez ahí, funciona bien y de forma eficiente.
- **Minor-a-Mayor:** botón de breakdown en dashboard Python no responde; mapa base de R no carga (causa confirmada: falta API key de CARTO).
- **Minor (patrón):** docstrings de R desactualizados respecto a valores default reales del código (2 casos + 1 copy-paste).
- **Minor-a-Mayor:** bug real de precedencia de operadores en `clean_gdf_boundaries()` (Python) — funciona por casualidad con geoBoundaries, roto para otros formatos que dice soportar.
- **Pista de causa raíz (no confirmada):** Python no filtra facilities sin coordenadas (a diferencia de R); podría deberse a que los formatos CSV (R) y GeoJSON (Python) de HDX no son snapshots equivalentes del mismo dataset.
- **Nota/recomendación positiva:** Python podría adoptar el enfoque de R para resolver URLs de descarga OSM (índice Geofabrik en vivo vs diccionario hardcodeado).
- **Nota:** `find_crs()` en R podría orientar la solución al problema de EPSG único.
- Lista extensa de hallazgos menores de instalación (`environment.yml`, `pyproject.toml`, dependencias faltantes), UX (leyenda log10, zoom inicial, filtros que se resetean, logo faltante) y calidad de código (hardcoded values, imports muertos, imprecisión de CRS sin reproyectar en dos archivos Python distintos) — ver `tester.md`.

## Qué falta

- TdR de la Unidad — no fue encontrado; se trabaja asumiendo la idea original en base a la documentación disponible.
- Investigación de causa raíz de la discrepancia de facilities R/Python — dejada conscientemente para el Developer en la próxima ronda (la revisión de código Python aportó una hipótesis concreta, ver arriba, pero no la confirmó).
- Unit tests de Python — confirmar estado real (la Acceptance Criteria ya admite que no existen).
- Otros modos de transporte (WALK, CAR) — solo se probó BICYCLE (default) en ambos lenguajes.
- Fuente alternativa de facilities (ej. registro oficial de Malawi vía función dedicada en R) — solo se usó healthsites.io en todos los casos.
- Reunión con la NSO para acordar recomendación (paso 4b).
- Completar y subir el Testing Recommendation Template.
- Preguntarle al Developer: si existen otras ramas de git con funcionalidad relevante no mergeada a `main` (como pasó con `r-subnational-workflow`); qué es la carpeta `src/healthcare_accessibility/experimental/` (10 archivos Python sin documentar en ninguna guía).
- Confirmar si existe el archivo `DESCRIPTION` en `src/r/dashboard/` (mencionado por la R User Guide, no confirmado en la revisión de código porque solo se subió la subcarpeta `R/`).
- **No requiere trabajo adicional:** compatibilidad multi-dispositivo — el Developer ya declaró explícitamente que recomienda uso en desktop; se puede cerrar como NOT TESTED/aceptado por criterio del Developer.

## Decisiones clave tomadas

- Se prioriza el workflow en **R antes que Python**, siguiendo el orden sugerido por el propio Developer en el Acceptance Criteria Template.
- Para las primeras corridas de prueba se usó **Malawi** (caso ya validado por el Developer) antes que Argentina, para aislar problemas de instalación de problemas de datos.
- **Argentina** se eligió como caso de país grande para cumplir los pedidos explícitos de la Acceptance Criteria ("Main workflow" y "Subnational run").
- **San Juan** se eligió para el caso subnacional por conveniencia práctica del Tester (facilities de ejemplo ya confirmadas, menor dependencia de fuentes externas) — el Developer no especificó una provincia; su propio ejemplo de referencia usa Buenos Aires.
- El testeo se hace en notebook personal sin permisos de administrador; todo el entorno técnico se instaló en el perfil de usuario, sin necesitar admin en ningún paso.
- Para Python, se pivotó a Miniconda (modo "Just Me", sin admin) al encontrar que `cykhash` (dependencia de `pyrosm`) no publica wheels precompilados para Windows en PyPI — solo vía conda-forge.
- Se reutilizó el mismo tipo de fuente (healthsites.io) para Malawi y Argentina, en ambos lenguajes, para que las comparaciones sean consistentes y no una variable de confusión por datos de origen distinto.
- Para el intento de Argentina en R, se descargó el CSV de HDX directamente en vez de convertir el GeoJSON de Python a CSV programáticamente, evitando la complejidad de manejar geometrías mixtas (punto/polígono) en R.
- Ante el hallazgo del EPSG único para Argentina (país multi-faja), se usó una aproximación práctica (EPSG:32720, UTM 20S) para poder continuar el testeo, documentando explícitamente que no es una solución real.
- Ante el hallazgo de la discrepancia de facilities R/Python, se decidió documentar el síntoma con evidencia exacta y no perseguir la causa raíz en este ciclo — corresponde al Developer investigarla, dado el tiempo disponible y que requiere contexto interno de desarrollo.
- Con la extensión de plazo en negociación (hasta el 9/9), se decidió sí completar la revisión de código fuente, unit tests de Python, y modos de transporte alternativos con el tiempo adicional; no se considera necesario testear compatibilidad multi-dispositivo dado que el Developer ya se pronunció al respecto.

## Documentos recibidos vs TdR

Los 4 documentos originales del Developer (Acceptance Criteria Template, Methodology, R User Guide, Python User Guide) son entregables suyos, no el TdR de la Unidad. El TdR no fue provisto ni encontrado hasta el momento.

## Diferencias R vs Python

Ambos workflows son implementaciones paralelas de la misma herramienta (requisito explícito del Acceptance Criteria). No son idénticos en configuración ni en comportamiento:

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r (jar v7.4 documentado) | r5py (jar v7.5.1 confirmado en uso) |
| **Facilities procesadas (Malawi, mismo tipo de fuente) — HALLAZGO CRÍTICO** | **152 total** | **299 total** |
| Resolución de URL de descarga OSM | Índice Geofabrik en vivo — robusto, sin mantenimiento manual | Diccionario hardcodeado país→continente — frágil, causó bug con Argentina |
| Límites administrativos | OpenStreetMap o archivo local | geoBoundaries (automático) |
| Asignación de celda a distrito | Configurable (zonal / raster / spatial join); incluye `find_crs()` para auto-UTM | No configurable |
| max_travel_time por defecto | 167 min (nota: roxygen2 interno dice 120, desactualizado) | 120 min |
| Descarga de centros de salud | Local o URL automática | Solo manual |
| Formatos de facilities soportados | CSV, Excel (no GeoJSON) | GeoJSON |
| CRS | Solo `crs` de salida (4326); sin problema de multi-faja para travel-time | Requiere `analysis_crs` proyectado por país — problemático en países multi-faja |
| Manejo de mayúsculas en columnas de facilities | Insensible (`rename_with(tolower)`) | No confirmado — asume nombres exactos |
| Chequeo temprano de límite de área del motor de ruteo | No existe — falla tarde y lento (mismo límite de 975.000 km² que Python, pero tras horas) | Sí — falla en segundos |
| Workflow subnacional | Existe y funciona bien y eficientemente, pero en rama separada (`r-subnational-workflow`) no mergeada a `main` y desactualizada | No implementado — la guía solo describe el approach en prosa (segmentación manual + buffer), sin herramienta dedicada |
| Mapa base del dashboard | Roto — falta API key de CARTO | Funcional, pero con botón de breakdown roto |
| Script extra opcional | — | `accessability_metrics.py` (sin equivalente en R) |
| Dashboard / mapas | Quarto + Shiny for R / Leaflet | Quarto + Shiny for Python / Folium |

## Documentación fuente

Los documentos originales provistos por el Developer se encuentran alojados en Drive:

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

## Entregables

Carpeta `entregables/`: contiene los archivos finales para enviar (por ejemplo, `slide.pptx` con el avance de testing, y en su momento el Testing Recommendation Template completo).

## Borrador del testeo (tester.md)

`tester.md`, en la raíz del repo: documento vivo donde vamos anotando, a medida que testeamos, todo lo que eventualmente va al **Testing Recommendation Template** oficial (hallazgos, evidencia de tests end-to-end, Proposed Amendments, checklists). Estructurado con las mismas secciones que el template real.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

Ramas relevantes: `main` (workflow principal, R y Python), `r-subnational-workflow` (workflow subnacional en R, no mergeada a `main`, desactualizada respecto a ella).

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión

---

## Historial breve de sesiones

- **13/08:** documentación inicial leída. Detectado bloqueo de acceso al repo.
- **19/08:** acceso restablecido vía equipo SIADS.
- **20/08:** clonado del repo confirmado exitoso.
- **24/08:** entorno técnico R instalado y verificado de punta a punta. Resuelto el bloqueante de datos de facilities (healthsites.io) y de boundaries (geoBoundaries local, tras fallo de Overpass API). **Pipeline R corrido end-to-end con éxito**: preprocesamiento, matrices de tiempo de viaje, y **dashboard confirmado visualmente**. Identificados 4 hallazgos menores.
- **25/08:** entorno Python resuelto vía Miniconda (pivote desde venv+pip). **Workflow Python validado 100% end-to-end**: `data_preparation.py`, `pop_travel_times.py`, y dashboard, con datos reales de Malawi. Identificados 6 hallazgos adicionales. Lección operativa sobre Ctrl+C accidental en terminal.
- **01/09:** Sesión extensa enfocada en el caso Argentina y comparación de paridad.
  - Entorno Python reconstruido, reproduciendo bugs de `environment.yml` y `pyproject.toml` con evidencia completa.
  - Hallazgo Mayor de EPSG único inadecuado para país multi-faja, resuelto con aproximación práctica.
  - Workflow nacional: Python falla rápido con causa exacta; R, en `main`, tarda órdenes de magnitud más en llegar al mismo tipo de error, tras investigar y descartar que fuera un freeze real (problema de repintado de ventana bajo presión de memoria).
  - Workflow subnacional: primer intento fallido por estar en la rama equivocada (`main` no implementa `network_source_path`); investigación del código fuente reveló la rama `r-subnational-workflow` con la implementación correcta; tras `git stash` + checkout + resolución de conflictos, San Juan corrió exitosamente en menos de 10 segundos.
  - **Comparación de paridad R vs Python con Malawi: hallazgo crítico de discrepancia de ~49% en facilities procesadas**, obtenido directamente por código tras descubrir que el botón de desglose del dashboard Python no respondía. Causa raíz no determinada, documentado para investigación del Developer.
  - Preparación de punteo para reunión con líderes locales del equipo Argentina.
- **02/09:** Confirmada atribución correcta de San Juan (decisión del Tester, no pedido específico del Developer). **Revisión de código fuente en R completada** (11 archivos, `src/r/dashboard/R/`): causa raíz del bug de mapa base confirmada (falta de API key de CARTO), patrón de docstrings desactualizados identificado (3 casos), hallazgo positivo sobre manejo de descargas OSM en R vs Python, función `find_crs()` identificada como posible pista de solución al hallazgo de CRS. Reconciliación completa de `tester.md` y `README.md` para asegurar que ninguna nota de sesiones anteriores se perdiera al ir resumiendo. **Revisión de código fuente en Python completada** (tarde, 7 archivos): bug real de precedencia de operadores en `clean_gdf_boundaries()`; hipótesis concreta con evidencia de código para la causa raíz de la discrepancia R/Python (Python no filtra facilities sin coordenadas); inconsistencia interna en validación de descargas HTTP; confirmación de que la leyenda log10 confusa se repite en mapas estáticos, no solo en el dashboard. Pregunta abierta sobre carpeta `experimental/` sigue sin resolver. Revisión de código fuente completada en ambos lenguajes.
