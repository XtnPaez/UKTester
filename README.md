# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## Última actualización de sesión

**Fecha:** 20/08/2026

**Qué hicimos:**
- Se armó el slide de avance de testing para el Cross-Partnership Quarterly Working Group (25/08), usando el template oficial de marca (layout de tres columnas: qué funciona bien / qué fue desafiante / próximos pasos).
- Se confirmó que el acceso al repositorio vía el equipo SIADS es **completo, no solo de lectura por navegador**: se pudo clonar `geospatial-healthcare-facilities` sin inconvenientes desde la máquina de Páez.
- Código de la Unidad ya disponible localmente para iniciar el testing de implementación.

**Bloqueante resuelto:**
El acceso al repositorio, restablecido el 19/08 vía SIADS, quedó confirmado como funcional al 100% tras el clonado exitoso.

**Próximos pasos pendientes:**
- Definir por dónde arrancar el testing de implementación: exploración de estructura general, checklist de código, o alguna de las 3 pruebas adicionales pedidas por el Developer.
- Definir cómo se comparte el código para su revisión (archivos puntuales o carpetas completas).
- Confirmar deadline real del slide para el Working Group del 25/08.
- Conseguir el TdR de la Unidad si el equipo logra localizarlo.
- Iniciar checklist de código (R y Python) y las 3 pruebas adicionales pedidas por el Developer (workflow R/Python, corrida subnacional en Argentina, workflow principal a nivel país).

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
