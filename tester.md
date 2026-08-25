# tester.md — Borrador acumulado para el Testing Recommendation Template

> Documento vivo. Acá vamos anotando, a medida que testeamos, todo lo que
> eventualmente va a volcarse al **Testing Recommendation Template** oficial.
> Las secciones siguen el mismo orden que el template real, para que llenarlo
> al final sea copiar y pegar, no reconstruir memoria.
>
> Última actualización: 24/08/2026

---

## Recommendation summary

| Campo | Valor |
| --- | --- |
| Title of Unit | 2.3.7 Health Facility Mapping |
| List of documents being tested | Acceptance Criteria Template, Methodology, R User Guide, Python User Guide |
| Developer country | UK |
| Tester country | Argentina |
| Recommendation | *(pendiente — no completar hasta cerrar todo el testing)* |
| Reason for recommendation | *(pendiente)* |

## Testing Overview

*(borrador, ampliar al final)*

- Tester: Cristian Páez (equipo Argentina).
- Documentación completa revisada antes de tocar código.
- Bloqueante de acceso al repositorio de código: sin acceso del 12/08 al 19/08 (una semana completa de la fase de testing).
- Entorno técnico R instalado y verificado en notebook sin permisos de administrador (R 4.4.0, Java 21 vía rJavaEnv, Quarto 1.9.38 portable).
- Pipeline R corrido end-to-end con datos reales, usando Malawi como caso de control (mismo país usado por el Developer como prototipo).
- Pendiente: repetir con Python, y correr con Argentina (caso pedido explícitamente por el Developer).

## Proposed Amendments

| Amendment description | Major / minor |
| --- | --- |
| El pipeline no crea automáticamente las carpetas de salida (`data/boundaries/`, `data/poi/`, `data/population/`, etc.). Si no existen previamente, `01_preprocess.R` falla con error de archivo/directorio no encontrado en vez de crearlas o dar un mensaje claro de qué falta. | Minor |
| La R User Guide documenta las columnas del CSV de healthsites.io como `x`, `y`, `osm_id` (minúscula). El archivo real descargado de HDX trae `X`, `Y` en mayúscula. No rompió el pipeline, pero la documentación no coincide exactamente con el dato real descargado. | Minor |
| La descarga automática de boundaries desde OpenStreetMap (Overpass API) falló por timeout/error 500 en nuestra prueba. Se resolvió usando un archivo local de geoBoundaries como fallback (camino ya contemplado por la guía), pero vale la pena que el Developer sepa que la vía automática puede no ser confiable y ofrecer el fallback más explícitamente en la documentación. | Minor |

---

## Testing criteria

### Suitability assessment

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Relevance | *(pendiente)* | |
| Accuracy | *(pendiente)* | |
| Technical accuracy | *(pendiente)* | |
| Prerequisite skills and knowledge | *(pendiente)* | |

### Structure and Organisation

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Headings and Subheadings | *(pendiente)* | |
| Logical Flow | *(pendiente)* | |
| Segmented content | *(pendiente)* | |
| Conciseness | *(pendiente)* | |

### Coherence

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Style Guide | *(pendiente)* | |
| Figure alignment | *(pendiente)* | |

### Accessibility

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Clarity | *(pendiente)* | |
| Terminology | *(pendiente)* | |
| Grammar and Spelling | *(pendiente)* | |
| Macros in spreadsheets | N/A — no aplica a esta Unidad | |

### QA checklist for code

| Criteria | R | Python | Action required / queries |
| --- | --- | --- | --- |
| Good coding practices (style, naming, logic, hardcoded values) | *(pendiente — pendiente lectura de código fuente)* | *(pendiente)* | |
| Code documentation (comentarios, roxygen2/docstrings) | *(pendiente)* | *(pendiente)* | |
| Data management (datos sensibles, accesibilidad de inputs) | *(pendiente)* | *(pendiente)* | |
| **You, the Tester, have tested the code from start to finish using one or more realistic end-to-end tests** | ✅ **PASS** — corrida completa `01_preprocess.R` + `02_ttm.R` con datos reales (Malawi): boundaries, facilities (healthsites.io), población (WorldPop), red de rutas construida (66.57s) y matriz de tiempo de viaje calculada (28.1s). Outputs `.csv` y `.parquet` generados correctamente. | ⏳ No iniciado | Evidencia completa en `data/ttm/malawi_closest_times.*` |
| Tested using alternative input data (para verificar que funciona con datos de otros usuarios) | ⏳ Parcial — se usaron datos reales de healthsites.io en vez de datos ficticios/de ejemplo, pero todavía no se probó con un segundo país/fuente distinta | *(pendiente)* | |
| Dependency management (librerías claras, memoria/procesamiento eficiente) | ✅ Dependencias documentadas correctamente en R User Guide; las 18 requeridas se instalaron sin fricción mayor (salvo conflicto de versión de `rlang`, resuelto reiniciando sesión) | *(pendiente)* | |

### QA checklist for interactive tools

| Criteria | Met? | Action required / queries |
| --- | --- | --- |
| Source code available, complies with QA checklist for code | *(pendiente)* | |
| README submitted, easy to follow | *(pendiente)* | |
| Interface clear and easy to understand | *(pendiente — falta ver el dashboard)* | |
| Expected outputs clearly communicated | *(pendiente)* | |
| Sensitive input data omitted/replaced | ✅ No sensitive data included (confirmado también por el propio Developer en Acceptance Criteria) | |
| Input data available to download | *(pendiente)* | |
| End-to-end test by Tester | *(pendiente — corresponde una vez visto el dashboard)* | |
| Tested with alternative input data | *(pendiente)* | |
| Compatible desktop/tablet/smartphone | *(pendiente)* | |
| Runs independently of OS | ✅ Corrido en Windows sin problemas hasta ahora | |
| Memory/processing efficiency | ✅ Malawi (país chico) corrió rápido y sin errores de memoria; pendiente confirmar con Argentina (país grande) | |

### Audio and video Products

N/A — la Unidad no incluye contenido audiovisual.

### Knowledge check / Quiz Products

*(pendiente confirmar si la Unidad incluye quiz)*

---

## Notas sueltas / para no perder

- Perdimos una semana completa (12/08–19/08) de la fase de testing por acceso al repositorio — relevante para justificar cronograma si hace falta.
- No se encontró TdR de la Unidad; se trabaja asumiendo la idea original según documentación disponible.
- Malawi elegido como caso de control por ser el mismo que usó el Developer como prototipo — minimiza riesgo de que un fallo sea "por los datos" en vez de "por el código".
- Argentina, al ser un país grande, probablemente requiera boundaries ADM2 (no ADM1) y estrategia subnacional, según lo ya documentado por el Developer para casos como Bangladesh.
