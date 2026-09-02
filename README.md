# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## Checkpoint actual

**Estamos en el paso 4a** (Tester testea el contenido) del proceso oficial. **Workflow R validado 100% end-to-end con Malawi, reconfirmado 01/09.** **Workflow Python validado 100% end-to-end con Malawi.** **Caso Argentina (pedido explícito del Developer) completo:**
- Workflow nacional: **FAIL esperado y confirmado en ambos lenguajes** (límite de área del motor r5), con causa raíz precisa.
- Workflow subnacional (San Juan): **PASS**, tras descubrir que la funcionalidad vive en una rama de git separada (`r-subnational-workflow`) no mergeada a `main`.

Falta: checklist formal de código en detalle (estilo/comentarios), comparación de paridad numérica R vs Python, y reunión con la NSO.

**Próximo hito real:** completar pasos 4a–4c y subir el Testing Recommendation Template — **deadline oficial: 4 de septiembre de 2026.**

*(Nota interna, no oficial: UK ofreció una extensión de plazo individual por el problema de acceso al repositorio, que se decidió no tomar formalmente, aunque queda disponible como respaldo si hiciera falta.)*

| Paso oficial (Content Testing Quick Guide) | Estado |
| --- | --- |
| 1. Developer sube Unidad + Acceptance Criteria | ✅ Hecho (lado Developer) |
| 2. UK team revisa Acceptance Criteria | ✅ Hecho |
| 3. UK team flaggea la Unidad al Tester | ✅ Hecho (7/08) |
| **4a. Tester testea el contenido** | 🔄 **En curso, muy avanzado** |
| 4b. Tester + NSO acuerdan recomendación | ⏳ No iniciado |
| 4c. Tester completa Testing Recommendation Template | ⏳ No iniciado |
| 5. Tester sube el Template | ⏳ Deadline oficial: 4/09/2026 |
| 6. UK team flaggea al Developer | — Futuro |
| 7. Moderation Panel (si rechazo) | — Futuro, condicional |
| 8. Sign-off en Project Board | — Futuro |

## Qué tenemos

- Los 6 documentos de referencia del Developer, más `docs/R/03a-subnational-workflow.md` de la rama `r-subnational-workflow`.
- Acceso completo y confirmado al repositorio de código.
- Entorno técnico R completo, instalado sin permisos de administrador. **Reconfirmado sano el 01/09.**
- **Pipeline R validado end-to-end con Malawi**, dashboard confirmado visualmente (con hallazgo nuevo: mapa base no carga, "API KEY REQUIRED" de CARTO).
- Entorno técnico Python completo vía Miniconda.
- **Pipeline Python validado end-to-end con Malawi**, dashboard confirmado visualmente.
- **Sesión 01/09 — caso Argentina completo:**
  - **Workflow nacional (ambos lenguajes): FAIL esperado y confirmado.** Python falla en segundos con `IllegalArgumentException: Geographic extent of street layer (6347812 km2) exceeds limit of 975000 km2`. R, en la rama `main`, tarda del orden de horas en llegar al mismo tipo de error (`Geographic extent of street layer exceeds limit of "975,000" km^2`) — sin ningún chequeo temprano equivalente al de Python, y sin indicadores de progreso que permitan al usuario estimar cuánto va a tardar.
  - **Workflow subnacional (San Juan): PASS**, tras un desvío importante — el primer intento en la rama `main` también falló (con el mismo error), porque el script `02_ttm.R` de `main` **no lee `network_source_path` ni `analysis_mode`**. Se descubrió que esta funcionalidad está implementada correctamente en la rama `r-subnational-workflow`, nunca mergeada a `main`. Tras hacer checkout de esa rama, el workflow subnacional corrió **exitosamente en menos de 10 segundos** de cómputo pesado (red construida en 4.18s, accesibilidad en 1.69s), usando un PBF recortado con `osmium-tool` (984 KB, vs 428 MB del país completo).
  - **Hallazgo mayor de EPSG único** para países multi-faja (`analysis_crs` en Python) — resuelto con aproximación práctica (EPSG:32720) para continuar el testeo.
  - Varios hallazgos adicionales de instalación y código — ver detalle en `tester.md`.

## Hallazgos para Proposed Amendments (Testing Recommendation Template)

Ver detalle completo, con evidencia y clasificación Major/Minor, en `tester.md`. Los más relevantes:

- **Mayor:** `analysis_crs` no soporta países grandes multi-faja como Argentina.
- **Mayor:** el workflow nacional de R no tiene chequeo temprano de extensión geográfica — tarda órdenes de magnitud más que Python en llegar al mismo error de límite de área.
- **Mayor (gestión de repo, no de funcionalidad):** el workflow subnacional de R vive en una rama (`r-subnational-workflow`) nunca mergeada a `main` y desactualizada respecto a ella. Una vez en la rama correcta, la funcionalidad en sí **funciona bien y de forma eficiente**.
- **Minor:** `environment.yml` con bug de sintaxis (reconfirmado).
- **Minor:** `pyproject.toml` sin metadata válida, instala paquete como "UNKNOWN" (reconfirmado).
- **Minor:** `importlib_metadata` no declarada, `health_data_source` hardcodeado, descarga OSM sin validar status code, fallback de `facility_type` faltante, `nbclient` faltante en instalación alternativa.
- **Minor:** dashboard Python no maneja con gracia datos faltantes de un país (`FileNotFoundError` crudo).
- **Minor-a-Mayor:** dashboard R no carga el mapa base ("API KEY REQUIRED" de CARTO).
- **Minor:** el filtrado de boundaries a un área subnacional por nombre de texto es insuficiente (departamentos homónimos entre provincias); el método correcto (centroide dentro del polígono) no está documentado.
- El resto de los hallazgos de la sesión previa (carpetas de salida no creadas automáticamente, columnas `X`/`Y` mayúscula, Overpass poco confiable, `ownership: NA`, CRS sin reproyectar en dos archivos, columna `id` requerida, warnings sin cuantificar, leyenda log10, zoom inicial del mapa) siguen vigentes — ver `tester.md`.

## Qué falta

- TdR de la Unidad — no fue encontrado.
- Checklist formal de código (R y Python) — revisión de estilo, comentarios y documentación de funciones en detalle.
- Confirmar que ambas implementaciones (R y Python) tienen funcionalidad idéntica — comparar resultados numéricos entre ambos workflows para el mismo caso (Malawi).
- Reunión con la NSO para acordar recomendación (paso 4b).
- Completar y subir el Testing Recommendation Template.
- Opcional: consultarle al Developer si existen otras ramas de git con funcionalidad relevante no mergeada a `main`, dado el precedente encontrado con `r-subnational-workflow`.

## Decisiones clave tomadas

- Se prioriza el workflow en **R antes que Python**, siguiendo el orden sugerido por el Developer.
- Malawi como caso de control antes que Argentina, para aislar problemas de instalación de problemas de datos.
- Argentina elegido como caso de país grande para cumplir los pedidos explícitos de la Acceptance Criteria ("Main workflow" y "Subnational run").
- San Juan elegido para el caso subnacional (en vez de Buenos Aires, el ejemplo de la guía) por tener facilities de ejemplo ya confirmadas y evitar depender de fuentes de boundaries adicionales.
- Ante el hallazgo de que la funcionalidad subnacional de R vive en una rama separada, se usó `git stash` para preservar la configuración de Argentina armada sobre `main` antes de hacer checkout de `r-subnational-workflow`, resolviendo los conflictos de merge resultantes a favor de la configuración ya armada.
- Ante el hallazgo del EPSG único para Argentina (país multi-faja), se usó una aproximación práctica (EPSG:32720, UTM 20S) para poder continuar el testeo, documentando explícitamente que no es una solución real.

## Diferencias R vs Python

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r (jar v7.4 documentado) | r5py (jar v7.5.1 confirmado en uso) |
| Límites administrativos | OpenStreetMap o archivo local | geoBoundaries (automático) |
| max_travel_time por defecto | 167 min | 120 min |
| Formatos de facilities soportados | CSV, Excel (no GeoJSON) | GeoJSON |
| CRS | Solo `crs` de salida (4326); sin problema de multi-faja porque no hay concepto de `analysis_crs` proyectado por país | Requiere `analysis_crs` proyectado por país — problemático en países multi-faja |
| Manejo de mayúsculas en columnas de facilities | Insensible (`rename_with(tolower)`) | No confirmado — asume nombres exactos |
| Chequeo temprano de límite de área geográfica | **No existe en `main`** — falla tarde y lento (horas). Confirmado como error de r5 subyacente, mismo límite que Python (975,000 km²) | Sí — falla en segundos con `IllegalArgumentException` |
| Workflow subnacional | Existe y funciona bien, pero en rama separada (`r-subnational-workflow`) no mergeada a `main` | No implementado — la Python User Guide solo describe el approach en prosa (segmentación manual + buffer), sin herramienta dedicada |
| Dashboard / mapas | Quarto + Shiny for R / Leaflet — mapa base con problema de API key | Quarto + Shiny for Python / Folium |

## Documentación fuente

Los documentos originales provistos por el Developer se encuentran alojados en Drive:

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

## Entregables

Carpeta `entregables/`: contiene los archivos finales para enviar.

## Borrador del testeo (tester.md)

`tester.md`, en la raíz del repo: documento vivo con todo el detalle de hallazgos, evidencia y checklists.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

Ramas relevantes: `main` (workflow principal, R y Python), `r-subnational-workflow` (workflow subnacional R, no mergeada a `main`, desactualizada).

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión

---

## Historial breve de sesiones

- **13/08:** documentación inicial leída. Detectado bloqueo de acceso al repo.
- **19/08:** acceso restablecido.
- **20/08:** clonado del repo confirmado exitoso.
- **24/08:** entorno técnico R instalado y verificado de punta a punta. **Pipeline R corrido end-to-end con éxito** con Malawi, dashboard confirmado visualmente.
- **25/08:** entorno Python resuelto vía Miniconda. **Workflow Python validado 100% end-to-end** con Malawi.
- **01/09:** Sesión enfocada en el caso Argentina completo (país grande, pedidos explícitos del Developer).
  - Entorno Python reconstruido desde cero, reproduciendo bugs conocidos de `environment.yml` y `pyproject.toml` con evidencia completa.
  - Hallazgo Mayor de EPSG único inadecuado para país multi-faja, resuelto con aproximación práctica (EPSG:32720).
  - Workflow nacional: Python falla rápido con causa exacta (975,000 km²); R, en `main`, tarda órdenes de magnitud más en llegar al mismo tipo de error, sin chequeo temprano.
  - Workflow subnacional: primer intento fallido por estar en la rama equivocada (`main` no implementa `network_source_path`); investigación del código fuente reveló la existencia de la rama `r-subnational-workflow` con la implementación correcta; tras `git stash` + checkout + resolución de conflictos, el workflow subnacional para San Juan corrió exitosamente en menos de 10 segundos.
  - Entorno R reconfirmado sano; dashboard R re-verificado con Malawi (hallazgo nuevo: mapa base no carga).
  - Pendiente: revisión formal de código fuente en ambos lenguajes, comparación de paridad numérica R vs Python.
