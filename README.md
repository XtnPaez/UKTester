# UK Tester

![Status](https://img.shields.io/badge/status-bloqueado-red)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## Última actualización de sesión

**Fecha:** 13/08/2026

**Qué hicimos:**
- Se cargaron y leyeron los 4 documentos del Developer para la Unidad 2.3.7 (Acceptance Criteria, Methodology, R User Guide, Python User Guide).
- Se generó el README inicial del proyecto.
- Se detectó que el repositorio de código (https://github.com/datasciencecampus/geospatial-healthcare-facilities) dejó de estar disponible (404) y que se perdió el acceso como colaborador a la organización Data Science Campus, pese a que el 12/08 el acceso funcionaba correctamente (incluido el PR #130).
- Se envió mail a Alex (Developer contact) reportando el problema con evidencia (timeline de acceso, 404, pérdida de membership, org y otros repos funcionando con normalidad). Sin respuesta aún.
- Se recibió una segunda tanda de los mismos 4 documentos (carpeta "Tester Files"), esta vez con las imágenes embebidas. Se comparó contra la versión anterior: mismo contenido textual y misma versión (07/08/2026 - First Submission); la única diferencia es que esta carpeta sí incluye capturas y diagramas que antes solo figuraban como texto alternativo en comentarios.
- Se verificó, con evidencia visual, que el alt text declarado en R User Guide y Python User Guide coincide con las imágenes reales (diagramas de flujo y capturas de WorldPop/HDX).
- Se confirmó que ninguno de los 4 documentos es el TdR (Terms of Reference) de la Unidad — no fue provisto hasta el momento.
- Se armó tabla comparativa de diferencias de implementación entre el workflow R y Python (ver sección "Diferencias R vs Python").

**Bloqueante activo:**
Sin acceso al repositorio de código, no se puede avanzar con el testing de implementación (checklist de código, ejecución de pipelines, pruebas end-to-end). A la espera de respuesta de Alex. Pendiente de reunión de equipo (13/08 14hs) por si alguna team leader del equipo Argentina tiene otra vía de resolución.

**Próximos pasos pendientes:**
- Esperar respuesta sobre el acceso al repositorio (o resolución alternativa surgida en la reunión de equipo).
- Conseguir el TdR de la Unidad si el equipo logra localizarlo.
- Una vez restablecido el acceso: iniciar checklist de código (R y Python) y las 3 pruebas adicionales pedidas por el Developer (workflow R/Python, corrida subnacional en Argentina, workflow principal a nivel país).

---

## Descripción

Repositorio de trabajo para el testing y evaluación de Unidades del Analysis for Action / Pandemic Preparedness Toolkit, a cargo de **UK Tester**. Este repo se usa para llevar el seguimiento del proceso de revisión: documentación recibida, criterios de aceptación, hallazgos, y evidencia de pruebas.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

Ruta original en Drive del Developer:
`UKTester\2.3.7 Health facility mapping - Paez\First submission\Developer files`

## Documentación fuente

Los documentos originales provistos por el Developer se encuentran alojados en Drive:

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

Estos mismos documentos también se conservan como copia en este repositorio, dentro de la carpeta correspondiente a la Unidad.

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Documentos recibidos vs TdR

Los 4 documentos recibidos (Acceptance Criteria Template, Methodology, R User Guide, Python User Guide) son entregables del Developer, no el TdR de la Unidad. El TdR (documento que define qué se le pidió al Developer antes de desarrollar) no fue provisto hasta el momento.

## Diferencias R vs Python

Ambos workflows son implementaciones paralelas de la misma herramienta (requisito explícito del Acceptance Criteria: deben existir en ambos lenguajes). No son idénticos en configuración:

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r | r5py |
| Límites administrativos | OpenStreetMap o archivo local | geoBoundaries (automático) |
| Asignación de celda a distrito | Configurable (zonal / raster / spatial join) | No configurable |
| max_travel_time por defecto | 167 min | 120 min |
| Descarga de centros de salud | Local o URL automática | Solo manual |
| CRS | Solo `crs` de salida (4326) | Además requiere `analysis_crs` proyectado por país |
| Script extra opcional | — | `accessability_metrics.py` (sin equivalente en R) |
| Dashboard / mapas | Quarto + Shiny for R / Leaflet | Quarto + Shiny for Python / Folium |

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión
