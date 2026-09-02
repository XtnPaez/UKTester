# UK Tester

![Status](https://img.shields.io/badge/status-en%20progreso-brightgreen)
![Unit](https://img.shields.io/badge/unit-2.3.7%20Health%20Facility%20Mapping-blue)
![Round](https://img.shields.io/badge/round-first%20submission-lightgrey)
![Languages](https://img.shields.io/badge/code-R%20%7C%20Python-informational)

## ⚠️ Hallazgo crítico de la sesión

**R y Python no son funcionalmente equivalentes.** Para el mismo país (Malawi) y el mismo tipo de fuente de datos (healthsites.io), procesan un número de facilities radicalmente distinto:

- **Total: 152 (R) vs 299 (Python) — ~49% de diferencia**
- Hospital: 71 (R) vs 195 (Python) — la categoría más afectada
- Esto se propaga a los resultados mostrados al usuario: 84.1% vs 76.1% de población fuera de rango; 18.4M vs 22.2M personas estimadas más allá del umbral, con el mismo filtro exacto (Nacional, clinic, 10km, Total population)

**Causa raíz no determinada** — documentado con evidencia numérica exacta y reproducible; se deja para que el Developer investigue en la próxima ronda. Ver detalle completo en `tester.md`.

## Checkpoint actual

**Estamos en el paso 4a** (Tester testea el contenido) del proceso oficial. Workflows R y Python validados end-to-end con Malawi y Argentina (nacional + subnacional). **Hallazgo crítico de falta de paridad entre implementaciones detectado y documentado** (ver arriba). Falta: checklist formal de código en detalle, y reunión con la NSO.

**Próximo hito real:** completar pasos 4a–4c y subir el Testing Recommendation Template — **deadline oficial: 4 de septiembre de 2026.**

| Paso oficial (Content Testing Quick Guide) | Estado |
| --- | --- |
| 1. Developer sube Unidad + Acceptance Criteria | ✅ Hecho (lado Developer) |
| 2. UK team revisa Acceptance Criteria | ✅ Hecho |
| 3. UK team flaggea la Unidad al Tester | ✅ Hecho (7/08) |
| **4a. Tester testea el contenido** | 🔄 **En curso, muy avanzado** |
| 4b. Tester + NSO acuerdan recomendación | ⏳ No iniciado |
| 4c. Tester completa Testing Recommendation Template | ⏳ No iniciado |
| 5. Tester sube el Template | ⏳ Deadline oficial: 4/09/2026 |

## Qué tenemos

- Documentación completa revisada, incluida `docs/R/03a-subnational-workflow.md` de la rama `r-subnational-workflow`.
- Entornos técnicos R y Python completos y funcionales, instalados sin permisos de administrador.
- **Pipelines R y Python validados end-to-end con Malawi**, ambos dashboards confirmados visualmente.
- **Caso Argentina (país grande, pedido explícito del Developer) completo:**
  - Workflow nacional: **FAIL esperado y confirmado en ambos lenguajes** (límite de área del motor r5, 975,000 km²). R tarda órdenes de magnitud más que Python en llegar al mismo resultado, sin chequeo temprano.
  - Workflow subnacional (San Juan): **PASS**, tras descubrir que la funcionalidad vive en la rama `r-subnational-workflow`, no mergeada a `main`. Una vez en la rama correcta, corrió exitosamente en menos de 10 segundos.
- **Comparación de paridad R vs Python con Malawi (mismo filtro exacto): hallazgo crítico de falta de equivalencia** — ver arriba y `tester.md` para el detalle completo.
- Hallazgos adicionales de UX y código: botón roto en dashboard Python, asset faltante, filtros que se resetean al recargar, mapa base de R sin cargar, y una lista extensa de hallazgos menores de instalación y calidad de código — ver `tester.md`.

## Hallazgos para Proposed Amendments (Testing Recommendation Template)

Ver detalle completo con evidencia y clasificación en `tester.md`. Los de mayor peso:

- **CRÍTICO/MAYOR:** discrepancia de ~49% en facilities procesadas entre R y Python para el mismo país — afecta directamente la confiabilidad de los resultados de accesibilidad.
- **Mayor:** `analysis_crs` no soporta países grandes multi-faja como Argentina.
- **Mayor:** el workflow nacional de R no tiene chequeo temprano de extensión geográfica.
- **Mayor (gestión de repo):** el workflow subnacional de R vive en una rama nunca mergeada a `main`. Una vez ahí, funciona bien.
- **Minor-a-Mayor:** botón de breakdown en dashboard Python no responde; mapa base de R no carga.
- Lista extensa de hallazgos menores de instalación (`environment.yml`, `pyproject.toml`, dependencias faltantes) y calidad de código — ver `tester.md`.

## Qué falta

- TdR de la Unidad — no fue encontrado.
- Checklist formal de código (R y Python) — revisión de estilo, comentarios y documentación de funciones en detalle.
- Investigación de causa raíz de la discrepancia de facilities R/Python — dejada conscientemente para el Developer en la próxima ronda.
- Reunión con la NSO para acordar recomendación (paso 4b).
- Completar y subir el Testing Recommendation Template.
- Opcional: consultarle al Developer si existen otras ramas de git con funcionalidad relevante no mergeada a `main`.

## Decisiones clave tomadas

- Malawi como caso de control, Argentina para cumplir los pedidos explícitos de país grande (nacional y subnacional).
- San Juan elegido para el caso subnacional por tener facilities de ejemplo ya confirmadas.
- Ante el hallazgo de la discrepancia de facilities entre R y Python, se decidió documentar el síntoma con evidencia exacta y no perseguir la causa raíz en este ciclo — el diagnóstico de por qué dos pipelines que leen la misma fuente llegan a conteos distintos requiere contexto interno de desarrollo que excede el alcance razonable del testing en este momento del cronograma.
- Ante el hallazgo del EPSG único para Argentina, se usó una aproximación práctica (EPSG:32720) para poder continuar el testeo.

## Diferencias R vs Python

| Aspecto | R | Python |
| --- | --- | --- |
| Motor de ruteo | r5r (jar v7.4 documentado) | r5py (jar v7.5.1 confirmado) |
| **Facilities procesadas (Malawi, mismo tipo de fuente)** | **152 total** | **299 total** |
| Límites administrativos | OpenStreetMap o archivo local | geoBoundaries (automático) |
| Formatos de facilities soportados | CSV, Excel (no GeoJSON) | GeoJSON |
| CRS | Solo `crs` de salida (4326) | Requiere `analysis_crs` proyectado por país — problemático en países multi-faja |
| Chequeo temprano de límite de área | No existe en `main` — falla tarde y lento | Sí — falla en segundos |
| Workflow subnacional | Existe y funciona bien, en rama separada no mergeada | No implementado — solo descrito en prosa |
| Dashboard | Quarto + Shiny for R / Leaflet — mapa base roto | Quarto + Shiny for Python / Folium — botón de breakdown roto |

## Documentación fuente

[https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6](https://drive.google.com/drive/u/1/folders/1Peo4XEoCPh-hz3CG3K_82CZYu04MXmx6)

## Borrador del testeo (tester.md)

`tester.md`, en la raíz del repo: documento vivo con todo el detalle de hallazgos, evidencia y checklists.

## Unidad bajo revisión

**2.3.7 Health Facility Mapping** — Developer: UK ONS

## Repositorio del desarrollo (código a evaluar)

[https://github.com/datasciencecampus/geospatial-healthcare-facilities](https://github.com/datasciencecampus/geospatial-healthcare-facilities)

Ramas relevantes: `main` (workflow principal), `r-subnational-workflow` (workflow subnacional R, no mergeada, desactualizada).

## Repositorio de trabajo (este)

[https://github.com/XtnPaez/UKTester](https://github.com/XtnPaez/UKTester)

## Flujo de trabajo

documentación → requisitos → criterios verificables → implementación → pruebas → evidencia → conclusión

---

## Historial breve de sesiones

- **13/08:** documentación inicial leída. Detectado bloqueo de acceso al repo.
- **19/08:** acceso restablecido.
- **20/08:** clonado del repo confirmado exitoso.
- **24/08:** entorno R instalado. Pipeline R corrido end-to-end con Malawi, dashboard confirmado.
- **25/08:** entorno Python resuelto. Workflow Python validado end-to-end con Malawi.
- **01/09:** Sesión extensa sobre el caso Argentina y comparación de paridad.
  - Workflow nacional: FAIL confirmado en ambos lenguajes (límite de área r5), con R mucho más lento que Python en llegar al mismo resultado.
  - Workflow subnacional: descubierta la rama `r-subnational-workflow` no mergeada a `main`; tras checkout, San Juan corrió exitosamente en menos de 10 segundos.
  - **Comparación de paridad R vs Python con Malawi: hallazgo crítico de discrepancia de ~49% en facilities procesadas**, con impacto directo en los resultados de accesibilidad mostrados al usuario. Causa raíz no determinada, documentado para investigación del Developer en próxima ronda.
  - Hallazgos adicionales de UX: botón roto en dashboard Python, asset faltante, filtros que se resetean al recargar, mapa base de R sin cargar.
  - Pendiente: revisión formal de código fuente en ambos lenguajes.
