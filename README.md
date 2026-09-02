# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## ⚠️ Hallazgo crítico de la sesión

**R y Python no son funcionalmente equivalentes.** Para el mismo país (Malawi) y el mismo tipo de fuente de datos, procesan un número de facilities radicalmente distinto:

- **Total: 152 (R) vs 299 (Python) — ~49% de diferencia**
- Hospital: 71 (R) vs 195 (Python) — la categoría más afectada
- Se propaga a los resultados: 84.1% vs 76.1% de población fuera de rango; 18.4M vs 22.2M personas estimadas más allá del umbral

**Causa raíz no determinada** — documentado con evidencia exacta, se deja para investigación del Developer. Ver detalle en `tester.md`.

## Checkpoint actual

**Paso 4a** del proceso oficial. Workflows R y Python validados end-to-end con Malawi y Argentina (nacional + subnacional). **Hallazgo crítico de falta de paridad detectado y documentado.** **Revisión de código fuente en R completada** (11 archivos), Python en curso. Falta: checklist de código Python, reunión con la NSO.

**Deadline oficial: 4 de septiembre de 2026** (extensión informal hasta el miércoles 9/9 en negociación con UK).

| Paso oficial | Estado |
| --- | --- |
| 1-3. Submission y flag inicial | ✅ Hecho |
| **4a. Tester testea el contenido** | 🔄 **En curso, muy avanzado** |
| 4b. Tester + NSO acuerdan recomendación | ⏳ No iniciado |
| 4c. Completar Testing Recommendation Template | ⏳ No iniciado |
| 5. Subir el Template | ⏳ Deadline 4/09 (posible extensión a 9/09) |

## Qué tenemos

- Entornos técnicos R y Python completos y funcionales, sin admin.
- **Pipelines R y Python validados end-to-end con Malawi**, ambos dashboards confirmados visualmente.
- **Caso Argentina completo:** workflow nacional FAIL confirmado en ambos lenguajes (límite de área del motor r5); workflow subnacional (San Juan) PASS, tras descubrir que la funcionalidad de R vive en la rama `r-subnational-workflow`, no mergeada a `main`.
- **Comparación de paridad R vs Python: hallazgo crítico de falta de equivalencia** — ver arriba.
- **Revisión de código fuente en R (11 archivos, `src/r/dashboard/R/`) completada:**
  - Calidad general buena: manejo de errores robusto, roxygen2 presente en la mayoría de las funciones.
  - Causa raíz confirmada del bug de mapa base: falta de API key de CARTO en `addProviderTiles`.
  - Patrón sistemático de docstrings desactualizados (2 casos de valores default incorrectos, 1 caso de copy-paste).
  - Hallazgo positivo: la descarga de OSM en R (vía índice Geofabrik) es más robusta que en Python (diccionario hardcodeado) — recomendación cruzada.
  - Nota: `find_crs()` en R podría ser punto de partida para resolver el problema de EPSG único en Python.
- Revisión de código Python: pendiente, en curso.

## Hallazgos para Proposed Amendments (Testing Recommendation Template)

Ver detalle completo en `tester.md`. Los de mayor peso:

- **CRÍTICO/MAYOR:** discrepancia de ~49% en facilities procesadas entre R y Python.
- **Mayor:** `analysis_crs` no soporta países multi-faja (Python).
- **Mayor:** workflow nacional de R sin chequeo temprano de extensión geográfica.
- **Mayor (gestión de repo):** workflow subnacional de R en rama no mergeada.
- **Minor:** causa raíz confirmada del bug de mapa base en R (falta API key CARTO).
- **Minor (patrón):** docstrings de R desactualizados respecto a valores default reales del código.
- **Nota/recomendación:** Python podría adoptar el enfoque de R para resolver URLs de OSM (índice Geofabrik en vez de diccionario hardcodeado).
- Lista extensa de hallazgos menores de instalación y UX — ver `tester.md`.

## Qué falta

- TdR de la Unidad — no encontrado.
- **Revisión de código fuente en Python** — en curso.
- Investigación de causa raíz de la discrepancia R/Python — dejada para el Developer.
- Reunión con la NSO (paso 4b).
- Completar y subir el Testing Recommendation Template.

## Decisiones clave tomadas

- Malawi como caso de control, Argentina para los pedidos explícitos de país grande.
- San Juan para el caso subnacional — el Developer no especificó provincia (su ejemplo usa Buenos Aires); San Juan se eligió por conveniencia práctica del Tester.
- Discrepancia de facilities R/Python: se documenta el síntoma con evidencia exacta, sin perseguir la causa raíz en este ciclo — corresponde al Developer investigarla.
- EPSG único para Argentina: se usó una aproximación práctica (EPSG:32720) para continuar el testeo.

## Diferencias R vs Python

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r (jar v7.4) | r5py (jar v7.5.1) |
| **Facilities procesadas (Malawi, mismo tipo de fuente)** | **152 total** | **299 total** |
| Resolución de URL de descarga OSM | Índice Geofabrik en vivo — robusto | Diccionario hardcodeado país→continente — frágil |
| CRS | Sin problema de multi-faja (no usa `analysis_crs` proyectado por país); incluye una función embrionaria de auto-selección UTM (`find_crs`) no usada para travel-time | Requiere `analysis_crs` proyectado por país — problemático en países multi-faja |
| Chequeo temprano de límite de área | No existe — falla tarde y lento | Sí — falla en segundos |
| Workflow subnacional | Existe y funciona bien, en rama separada no mergeada | No implementado — solo descrito en prosa |
| Mapa base del dashboard | Roto — falta API key de CARTO (`addProviderTiles("CartoDB.Positron")`) | Funcional |
| Documentación interna del código (roxygen2/docstrings) | Presente pero con casos de desactualización respecto al código real | Presente, con hallazgos puntuales (import muerto, hardcoded values) |

## Documentación fuente

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

## Borrador del testeo (tester.md)

`tester.md`, en la raíz del repo: documento vivo con todo el detalle de hallazgos, evidencia y checklists.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

Ramas relevantes: `main`, `r-subnational-workflow` (no mergeada, desactualizada).

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión

---

## Historial breve de sesiones

- **13/08 – 25/08:** documentación revisada, acceso al repo resuelto, entornos R y Python instalados y validados end-to-end con Malawi.
- **01/09:** Sesión extensa sobre Argentina — workflow nacional (FAIL confirmado en ambos lenguajes), workflow subnacional (descubierta la rama `r-subnational-workflow`, San Juan corrido exitosamente), y **comparación de paridad R vs Python con hallazgo crítico** de discrepancia de facilities.
- **02/09:** Punteo preparado para reunión con líderes locales. **Revisión de código fuente en R completada** (11 archivos): causa raíz del bug de mapa base confirmada, patrón de docstrings desactualizados identificado, hallazgo positivo sobre manejo de descargas OSM en R vs Python. Revisión de código Python en curso.
