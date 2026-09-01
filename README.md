# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## Checkpoint actual

**Estamos en el paso 4a** (Tester testea el contenido) del proceso oficial. **Workflow R validado 100% end-to-end con Malawi, reconfirmado 01/09.** **Workflow Python validado 100% end-to-end con Malawi.** **Caso Argentina (pedido explícito del Developer) en curso**: workflow nacional en Python confirmado como FAIL esperado (límite de área del motor r5), con evidencia técnica precisa. Workflow nacional en R en curso de verificación. Falta: corrida subnacional (Argentina), checklist formal de código en detalle (estilo/comentarios), y reunión con la NSO.

**Próximo hito real:** completar pasos 4a–4c y subir el Testing Recommendation Template — **deadline oficial: 4 de septiembre de 2026.**

*(Nota interna, no oficial: se negoció informalmente con la jefa de equipo Argentina; UK ofreció una extensión de plazo individual por el problema de acceso al repositorio, que se decidió no tomar formalmente, aunque queda disponible como respaldo si hiciera falta.)*

| Paso oficial (Content Testing Quick Guide) | Estado |
| --- | --- |
| 1. Developer sube Unidad + Acceptance Criteria | ✅ Hecho (lado Developer) |
| 2. UK team revisa Acceptance Criteria | ✅ Hecho |
| 3. UK team flaggea la Unidad al Tester | ✅ Hecho (7/08) |
| **4a. Tester testea el contenido** | 🔄 **En curso** |
| 4b. Tester + NSO acuerdan recomendación | ⏳ No iniciado |
| 4c. Tester completa Testing Recommendation Template | ⏳ No iniciado |
| 5. Tester sube el Template | ⏳ Deadline oficial: 4/09/2026 |
| 6. UK team flaggea al Developer | — Futuro |
| 7. Moderation Panel (si rechazo) | — Futuro, condicional |
| 8. Sign-off en Project Board | — Futuro |

## Qué tenemos

- Los 6 documentos de referencia (Acceptance Criteria, Methodology, R User Guide, Python User Guide, Content Testing Quick Guide, Testing Recommendation Template).
- Acceso completo y confirmado al repositorio de código (clonado exitoso, 20/08).
- Slide de avance de testing para el Working Group, listo y aprobado (ver carpeta `entregables/`).
- Entorno técnico R completo y verificado, instalado sin permisos de administrador: R 4.4.0, Java 21 (vía rJavaEnv), Quarto 1.9.38 (portable), rJava, y los 18 paquetes R requeridos por la guía. **Reconfirmado sano el 01/09, sin necesidad de reinstalar nada.**
- **Pipeline R validado end-to-end con datos reales (caso Malawi, 24/08, reconfirmado 01/09):**
  - `01_preprocess.R`: boundaries (geoBoundaries ADM1), facilities (healthsites.io vía HDX, 149 filas sin coordenadas descartadas automáticamente — comportamiento esperado), y los 6 rasters demográficos de WorldPop + stack combinado. Todo generado correctamente.
  - `02_ttm.R`: red de rutas construida en 66.57s, matriz de tiempo de viaje calculada en 28.1s. Outputs `malawi_closest_times.csv` (~95MB) y `.parquet` (~13MB) generados sin errores.
- **Dashboard R confirmado visualmente (24/08, reconfirmado 01/09):** `quarto preview` levantó el dashboard Shiny sin errores. Controles de distrito, tipo de facility, distancia y grupo demográfico funcionan como documenta la Methodology. Probado con Central Region: 10 hospitales, 87% de población fuera de 8km, 8,208,511 personas estimadas más allá del umbral, popups de facility individual funcionando. **Hallazgo nuevo (01/09): el mapa base no carga** — se ve el placeholder "API KEY REQUIRED" de CARTO en vez de un mapa de calles/relieve (ver Hallazgos).
- **Entorno técnico Python completo y verificado (25/08):** Python 3.11.16 vía Miniconda (instalado sin admin, modo "Just Me"), entorno `hc-mapping` creado desde `environment.yml` con todas las dependencias de conda-forge (r5py, osmnx, pyrosm, cykhash, geopandas, etc.) más `pip_system_certs` agregado a mano.
- **`data_preparation.py` validado end-to-end con datos reales (Malawi, 25/08):** exit code 0. Los 5 outputs esperados por la guía confirmados.
- **`pop_travel_times.py` validado end-to-end con datos reales (Malawi, 25/08):** exit code 0. Cálculo de tiempos de viaje en 75.64s (comparable a R).
- **Dashboard Python confirmado visualmente (25/08):** `quarto render` + `shiny run` funcionaron sin errores. Vista nacional, hospital, 10km: 82.7% de población fuera de rango, 24,117,974 personas estimadas más allá del umbral. **Workflow Python 100% validado end-to-end con Malawi.**
- **Sesión 01/09 — caso Argentina (pedido explícito del Developer para país grande):**
  - Entorno Python reconstruido en la misma notebook desde cero (bugs de `environment.yml` y `pyproject.toml` reproducidos y reconfirmados con traceback completo).
  - `data_preparation.py` corrido con éxito para Argentina, con soporte de país nuevo agregado manualmente (`country_continent_dict`, `analysis_crs`).
  - **Hallazgo mayor:** ningún EPSG proyectado único cubre Argentina con precisión aceptable (país multi-faja); se usó EPSG:32720 (UTM 20S) como aproximación práctica.
  - `pop_travel_times.py` **falló según lo esperado**, con causa raíz precisa: `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2` — límite de diseño del motor r5 (Java), no memoria RAM como sugería la Acceptance Criteria.
  - Dashboard Python: confirmado que no maneja con gracia la ausencia de datos de un país (`FileNotFoundError` crudo).
  - Workflow R: se intentó reproducir el mismo caso. Facilities descargadas en CSV desde HDX; confirmado que el cleaning code de R (`rename_with(tolower)`) es insensible a mayúsculas/minúsculas, resolviendo una duda pendiente desde el 24/08. `01_preprocess.R` en curso al cierre de esta sesión.

## Hallazgos para Proposed Amendments (Testing Recommendation Template)

Ver detalle completo, con evidencia y clasificación Major/Minor, en `tester.md`. Resumen de los más relevantes:

- **Mayor:** `analysis_crs` no soporta países grandes multi-faja como Argentina — limitación de diseño, no un bug puntual.
- **Minor:** `environment.yml` con bug de sintaxis en la sección `pip:` (reconfirmado 01/09 con un segundo intento independiente).
- **Minor:** `pyproject.toml` sin metadata válida, instala paquete como "UNKNOWN" (reconfirmado 01/09).
- **Minor:** `data_preparation.py` importa `importlib_metadata` sin declararla como dependencia, para un objeto que nunca se usa.
- **Minor:** `health_data_source` hardcodeado en `data_preparation.py`, contradice el criterio de "hardcoded values removed" marcado como cumplido por el DP.
- **Minor:** descarga de OSM sin validar el código de respuesta HTTP antes de guardar el archivo.
- **Minor:** pérdida de `facility_type` cuando el tag `amenity` viene vacío (falta fallback a `healthcare`), confirmado con datos reales de Argentina.
- **Minor:** método de instalación alternativo (plan B) no instala `nbclient`, necesario para el dashboard.
- **Minor:** dashboard Python no maneja con gracia la ausencia de datos de un país.
- **Minor:** `data_preparation.py` no confirma su finalización exitosa.
- **Minor:** documentación no especifica requisitos de memoria/hardware según tamaño de país.
- **Minor-a-Mayor:** dashboard R no carga el mapa base (placeholder "API KEY REQUIRED" de CARTO).
- El resto de los hallazgos de la sesión 24-25/08 (carpetas de salida no creadas automáticamente, columnas `X`/`Y` mayúscula, Overpass poco confiable, `ownership: NA`, CRS sin reproyectar en dos archivos, columna `id` requerida, warning de puntos sin conectar, leyenda log10, zoom inicial del mapa) siguen vigentes — ver `tester.md`.

## Qué falta

- TdR de la Unidad — no fue encontrado; se trabaja asumiendo la idea original en base a la documentación disponible y una primera lectura del código.
- Confirmar resultado de `01_preprocess.R` y `02_ttm.R` con Argentina en R (en curso al cierre de la sesión 01/09).
- **Corrida subnacional en Argentina** (San Juan u otra provincia) — pedido explícito del Developer, aún no iniciado.
- Checklist formal de código (R y Python) — revisión de estilo, comentarios y documentación de funciones en detalle, más allá de los hallazgos puntuales encontrados al pasar.
- Confirmar que ambas implementaciones (R y Python) tienen funcionalidad idéntica — comparar resultados numéricos entre ambos workflows para el mismo caso (Malawi).
- Reunión con la NSO para acordar recomendación (paso 4b).
- Completar y subir el Testing Recommendation Template.

## Decisiones clave tomadas

- Se prioriza el workflow en **R antes que Python**, siguiendo el orden sugerido por el propio Developer en el Acceptance Criteria Template.
- Para las primeras corridas de prueba se usó **Malawi** (caso ya validado por el Developer) antes que Argentina, para aislar problemas de instalación de problemas de datos.
- **Argentina** se eligió como caso de país grande para cumplir el pedido explícito de la Acceptance Criteria ("Main workflow" y "Subnational run").
- El testeo se hace en notebook personal sin permisos de administrador; todo el entorno técnico (R, Java, Quarto, paquetes) se instaló en el perfil de usuario, sin necesitar admin en ningún paso.
- Para Python, se pivotó a Miniconda (modo "Just Me", sin admin) al encontrar que `cykhash` (dependencia de `pyrosm`) no publica wheels precompilados para Windows en PyPI — solo vía conda-forge.
- Se reutilizó el mismo tipo de fuente (healthsites.io vía HDX) para Malawi y Argentina, en ambos lenguajes, para que las comparaciones sean consistentes y no una variable de confusión por datos de origen distinto.
- Para el intento de Argentina en R, se descargó el CSV de HDX directamente en vez de convertir el GeoJSON de Python a CSV programáticamente, evitando la complejidad de manejar geometrías mixtas (punto/polígono) en R.
- Ante el hallazgo del EPSG único para Argentina (país multi-faja), se decidió usar una aproximación práctica (EPSG:32720, UTM 20S) para poder continuar el testeo, documentando explícitamente que no es una solución real sino un compromiso para destrabar el trabajo.

## Documentos recibidos vs TdR

Los 4 documentos originales del Developer (Acceptance Criteria Template, Methodology, R User Guide, Python User Guide) son entregables suyos, no el TdR de la Unidad. El TdR no fue provisto ni encontrado hasta el momento.

## Diferencias R vs Python

Ambos workflows son implementaciones paralelas de la misma herramienta (requisito explícito del Acceptance Criteria: deben existir en ambos lenguajes). No son idénticos en configuración:

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r (jar v7.4 documentado) | r5py (jar v7.5.1 confirmado en uso, 01/09) |
| Límites administrativos | OpenStreetMap o archivo local | geoBoundaries (automático) |
| Asignación de celda a distrito | Configurable (zonal / raster / spatial join) | No configurable |
| max_travel_time por defecto | 167 min | 120 min |
| Descarga de centros de salud | Local o URL automática | Solo manual |
| Formatos de facilities soportados | CSV, Excel (no GeoJSON) | GeoJSON (vía script propio) |
| CRS | Solo `crs` de salida (4326) | Además requiere `analysis_crs` proyectado por país |
| Manejo de nombres de columna en facilities | Insensible a mayúsculas/minúsculas (`rename_with(tolower)`) | No confirmado — asume nombres exactos (`osm_id`, no `OSM_ID`) |
| Límite de área geográfica del motor de ruteo | No confirmado independientemente para Argentina (ver Qué falta) | Confirmado: 975,000 km² (motor r5) |
| Script extra opcional | — | `accessability_metrics.py` (sin equivalente en R) |
| Dashboard / mapas | Quarto + Shiny for R / Leaflet | Quarto + Shiny for Python / Folium |

## Documentación fuente

Los documentos originales provistos por el Developer se encuentran alojados en Drive:

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

Estos mismos documentos también se conservan como copia en este repositorio, dentro de la carpeta correspondiente a la Unidad.

## Entregables

Carpeta `entregables/`: contiene los archivos finales para enviar (por ejemplo, `slide.pptx` con el avance de testing para el Working Group, y en su momento el Testing Recommendation Template completo).

## Borrador del testeo (tester.md)

`tester.md`, en la raíz del repo: documento vivo donde vamos anotando, a medida que testeamos, todo lo que eventualmente va al **Testing Recommendation Template** oficial (hallazgos, evidencia de tests end-to-end, Proposed Amendments, checklists). Estructurado con las mismas secciones que el template real, para volcarlo directo cuando el testing esté avanzado o cerrado, sin tener que reconstruir memoria.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

Ruta original en Drive del Developer:
`UKTester\2.3.7 Health facility mapping - Paez\First submission\Developer files`

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión

---

## Historial breve de sesiones

- **13/08:** documentación inicial leída. Detectado bloqueo de acceso al repo.
- **19/08:** acceso restablecido vía equipo SIADS.
- **20/08:** clonado del repo confirmado exitoso. Slide inicial armado.
- **24/08:** recibidos Content Testing Quick Guide y Testing Recommendation Template. Confirmado deadline oficial (4/09). Entorno técnico R instalado y verificado de punta a punta. Resuelto el bloqueante de datos de facilities (healthsites.io vía HDX) y de boundaries (geoBoundaries local, tras fallo de Overpass API). **Pipeline R corrido end-to-end con éxito**: preprocesamiento, matrices de tiempo de viaje, y **dashboard confirmado visualmente**. Workflow R 100% validado. Identificados 4 hallazgos menores para Proposed Amendments. Creado `tester.md`.
- **25/08:** entorno Python resuelto vía Miniconda. **Workflow Python validado 100% end-to-end**: `data_preparation.py`, `pop_travel_times.py`, y dashboard, todos con datos reales de Malawi. Identificados 6 hallazgos adicionales para Proposed Amendments.
- **01/09:** Sesión enfocada en el caso Argentina (país grande, pedido explícito del Developer). Entorno Python reconstruido desde cero en la misma notebook, reproduciendo con evidencia completa los bugs de `environment.yml` y `pyproject.toml` ya conocidos. Resueltos varios bloqueos nuevos: dependencia `importlib_metadata` faltante, EPSG único inadecuado para país multi-faja (hallazgo **Mayor**, resuelto con aproximación práctica EPSG:32720), y `nbclient` faltante para el dashboard vía instalación alternativa. `data_preparation.py` corrido con éxito para Argentina en Python; `pop_travel_times.py` **falló según lo esperado por el Developer**, con causa raíz precisa identificada (límite de área del motor r5, 975,000 km², no memoria RAM genérica). Dashboard Python confirmado que falla sin gracia ante datos faltantes. Entorno R reconfirmado sano sin reinstalar nada; dashboard R re-verificado con Malawi (con hallazgo nuevo: mapa base no carga, "API KEY REQUIRED"). Iniciado intento de reproducir Argentina en R: resuelta duda pendiente sobre sensibilidad a mayúsculas en columnas de facilities (el código R es insensible, correctamente); `01_preprocess.R` en curso al cierre de la sesión. Pendiente: resultado de R con Argentina, corrida subnacional, y revisión formal de código fuente en ambos lenguajes.
