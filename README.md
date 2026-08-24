# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## Checkpoint actual

**Estamos en el paso 4a** (Tester testea el contenido) del proceso oficial. Código accesible, **entorno técnico R completo y verificado**. Falta entorno Python, configuración con caso de prueba, y checklist técnico de código.

**Próximo hito real:** completar pasos 4a–4c y subir el Testing Recommendation Template — **deadline oficial: 4 de septiembre de 2026.**

*(Nota interna, no oficial: se negoció informalmente con la jefa de equipo Argentina apuntar al viernes 28/08 como fecha de entrega interna, previa a la oficial, para que el equipo técnico de Argentina revise antes de enviar.)*

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
- **Entorno técnico R completo y verificado**, instalado sin permisos de administrador: R 4.4.0, Java 21 (vía rJavaEnv), Quarto 1.9.38 (portable), rJava, y los 18 paquetes R requeridos por la guía. Paquete local del dashboard (`src/r/dashboard`) carga sin errores.

## Qué falta

- TdR de la Unidad — no fue encontrado; se trabaja asumiendo la idea original en base a la documentación disponible y una primera lectura del código.
- Puesta a punto de entorno técnico Python — no iniciada.
- Configurar `config.yaml` con caso de prueba (Malawi) y correr el pipeline R end-to-end (preprocesamiento, matrices de tiempo de viaje, dashboard).
- Checklist de código (R y Python) del Testing Recommendation Template.
- Confirmar que ambas implementaciones (R y Python) tienen funcionalidad idéntica.
- Corridas con Argentina — evaluando rendimiento con volúmenes de datos pesados, probablemente con estrategia de menor a mayor (subnacional antes que país completo) dado el tamaño del territorio.
- Reunión con la NSO para acordar recomendación (paso 4b).
- Completar y subir el Testing Recommendation Template.

## Decisiones clave tomadas

- Se prioriza el workflow en **R antes que Python**, siguiendo el orden sugerido por el propio Developer en el Acceptance Criteria Template.
- Para las primeras corridas de prueba se usa **Malawi** (caso ya validado por el Developer) antes que Argentina, para aislar problemas de instalación de problemas de datos.
- El deadline del viernes 28/08 es un acuerdo informal con la jefa de equipo Argentina, no el deadline oficial (que es el 4/09) — se mantiene así frente al equipo local, sin comunicarlo como oficial hacia UK.
- El testeo se hace en notebook personal sin permisos de administrador; todo el entorno técnico (R, Java, Quarto, paquetes) se instaló en el perfil de usuario (vía versiones portables y `install.packages()`), sin necesitar admin en ningún paso.

## Documentos recibidos vs TdR

Los 4 documentos originales del Developer (Acceptance Criteria Template, Methodology, R User Guide, Python User Guide) son entregables suyos, no el TdR de la Unidad. El TdR no fue provisto ni encontrado hasta el momento.

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

## Documentación fuente

Los documentos originales provistos por el Developer se encuentran alojados en Drive:

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

Estos mismos documentos también se conservan como copia en este repositorio, dentro de la carpeta correspondiente a la Unidad.

## Entregables

Carpeta `entregables/`: contiene los archivos finales para enviar (por ejemplo, `slide.pptx` con el avance de testing para el Working Group del 25/08, y en su momento el Testing Recommendation Template completo).

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
- **24/08:** recibidos Content Testing Quick Guide y Testing Recommendation Template (proceso oficial y entregable final). Confirmado deadline oficial (4/09). Slide de avance rediseñado y aprobado para el Working Group. Entorno técnico R instalado y verificado de punta a punta en notebook sin admin (R, Java 21, Quarto, paquetes). Próximo paso: configurar caso Malawi y correr el pipeline.
