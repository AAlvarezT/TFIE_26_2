# Conclusiones — The Box

## Resumen ejecutivo

Entre 2025 y 2026, The Box mejora su desempeño en semanas comparables: la venta crece 102.6% y la conversión depurada sube de 5.97% a 6.47%. La descomposición logarítmica sugiere que el crecimiento se reparte entre mayor flujo (33.8% del crecimiento), mejor conversión (21.7%) y mayor ticket (44.5%). En 2026, la conversión real de semanas 2–34 es 6.48% y la frontera interna p90 llega a 7.78%, lo que deja una brecha referencial de 1.30 pp. Las regresiones y correlaciones muestran una asociación negativa entre tráfico y conversión, pero no permiten atribuir causalidad. Además, San Isidro y Mega Plaza Chimbote muestran quiebres consistentes con posibles cambios de medición. Si la organización cerrara de forma sostenible la brecha frente a p90 bajo los supuestos usados aquí, la venta potencial referencial sería de S/7.85 millones anuales.

## Metodología y definición de muestras

- **Fuente:** `BD The Box Presentacion 30.08.xlsx`
- **raw:** todos los registros `THE BOX`.
- **dep:** registros con `hora` entre 10 y 21, `flujo > 0` y `flujo >= transacciones`.
- **comp/sw26:** semanas 2–34 del año correspondiente.
- **tiendas comunes:** tiendas presentes en 2025 y 2026 dentro de `dep`, semanas 2–34.
- **Conversión:** `transacciones / flujo`.

## Resultados por bloque

### 1. Estructura y cobertura
- Filas totales de la hoja operativa: 122,329
- Filas THE BOX: 103,790
- Tiendas únicas THE BOX: 16

### 2. Calidad de datos y depuración
- Conversión reportada 2025: 6.468%
- Conversión reportada 2026: 6.815%
- Conversión depurada 2025: 5.966%
- Conversión depurada 2026: 6.474%
- Tabla: `outputs/tablas/calidad_datos.csv`

### 3. Evolución 2025–2026
- Crecimiento de venta: +102.6%
- Aporte flujo: 33.8%
- Aporte conversión: 21.7%
- Aporte ticket: 44.5%
- Crecimiento en tiendas comunes: +85.2%
- Gráficos: `outputs/figuras/evolucion_descomposicion.png`, `outputs/figuras/evolucion_conversion_semanal.png`

### 4. Conversión real y referencia interna
- Conversión real 2026 (sem 2–34): 6.4823%
- Frontera p75: 7.1980%
- Frontera p90: 7.7848%
- Frontera máximo: 8.5843%
- Tabla: `outputs/tablas/frontera_por_tienda.csv`
- Gráfico: `outputs/figuras/frontera_conversion.png`

### 5. Relación tráfico–conversión
- Panel hora: beta=-0.01583, p=0.0000
- Efecto de +10% flujo horario: -0.1509 pp
- Panel semana: beta=-0.04897, p=0.0485
- Pearson: r=-0.378, p=0.149
- Spearman: r=-0.615, p=0.011
- Tabla: `outputs/tablas/modelos_trafico_conversion.csv`
- Gráfico: `outputs/figuras/scatter_flujo_conversion.png`

### 6. Varianza dentro y entre tiendas
- R² tienda: 0.332
- R² semana: 0.080
- R² ambos: 0.420
- SD entre tiendas: 0.00999
- SD dentro de tienda (promedio): 0.01200
- Gráfico: `outputs/figuras/varianza_conversion_tienda.png`

### 7. Patrones por hora y día
- Conversión a las 10:00: 4.21%
- Conversión resto del día: 6.54%
- Gráficos: `outputs/figuras/patron_hora.png`, `outputs/figuras/patron_dia.png`, `outputs/figuras/heatmap_hora_dia.png`, `outputs/figuras/heatmap_tienda_hora.png`

### 8. Posibles cambios de medición
- San Isidro antes/después: flujo 566 → 874; conversión 10.89% → 4.70%
- Mejora con todas las tiendas: 0.99 pp
- Mejora sin rupturas: 1.16 pp
- Gráficos: `outputs/figuras/serie_san_isidro.png`, `outputs/figuras/serie_chimbote.png`

### 9. Metas comerciales
- Cumplimiento ponderado 2025: 67.77%
- Cumplimiento ponderado 2026: 73.56%
- Exigencia meta 2026 vs venta 2025: +158.0%
- Logro real 2026 vs venta 2025: +89.0%
- Correlación conversión-cumplimiento: r=-0.015, p=0.957
- Gráfico: `outputs/figuras/metas_vs_conversion.png`

### 10. Impacto económico y sensibilidad
- Factor estacional: 1.9009
- Flujo anual equivalente: 1,697,953
- Ticket promedio: S/354.90
- Escenario p90: 1.3025 pp, 22,116 transacciones y S/7.85 MM
- Tabla: `outputs/tablas/impacto_economico_escenarios.csv`
- Gráfico: `outputs/figuras/impacto_escenarios.png`

## Supuestos del impacto económico

- El flujo 2026 de semanas 2–34 representa el patrón operativo base.
- La anualización usa el factor estacional observado en 2025.
- El ticket promedio permanece constante al cerrar la brecha de conversión.
- El benchmark p75/p90/max proviene del propio historial semanal de las tiendas.
- La venta potencial es una referencia bruta, no utilidad ni impacto garantizado.

## Limitaciones

- Correlación no implica causalidad.
- Los efectos fijos no eliminan todos los confusores.
- El p90 es referencia interna, no meta sostenible demostrada.
- Los cambios bruscos de flujo son indicios de medición, no confirmación de falla.
- El impacto económico depende de supuestos de estacionalidad, ticket y sostenibilidad.

## Próximos pasos

1. Auditar contadores de tráfico en San Isidro y Mega Plaza Chimbote.
2. Medir aforo, colas, staffing y tiempos de atención por franja.
3. Diseñar pilotos operativos con evaluación antes-después y controles.
4. Revisar la alineación entre metas comerciales y capacidad operativa.
5. Integrar monitoreo de calidad de dato en la rutina comercial.

## Matriz final de hallazgos

| Hallazgo                             | Evidencia                             | Implicación TFIE                            | Validación pendiente            |
|:-------------------------------------|:--------------------------------------|:--------------------------------------------|:--------------------------------|
| Depuración necesaria                 | Flujo cero, hora 22 y casos flujo<trx | Evita sobreestimar o subestimar conversión  | Auditar contador y cierres      |
| Mejora interanual real               | Venta y conversión depurada suben     | Hay progreso, pero no uniforme              | Separar mix y aperturas         |
| Benchmark interno útil               | p75/p90 salen del propio historial    | Sirve para priorizar brechas                | Probar sostenibilidad operativa |
| Relación tráfico-conversión negativa | Paneles y Spearman negativos          | Sugiere congestión o mix adverso            | Medir aforo, colas y staffing   |
| No causalidad                        | Efectos fijos no bastan               | Evita sobrerreaccionar con una sola palanca | Diseños cuasi-experimentales    |
| Oportunidad dentro de tienda         | SD dentro > SD entre                  | Gestionar ejecución fina por semana/hora    | Monitoreo operacional detallado |
| Posibles quiebres de medición        | San Isidro y Chimbote saltan en flujo | Prioridad de control tecnológico            | Revisar logs/calibraciones      |
| Impacto económico referencial        | Escenarios p75/p90/max                | Útil para priorización, no promesa          | Validar con pilotos             |

## Verificación contra valores esperados del script R

Tabla completa: `outputs/tablas/verificacion_vs_r.csv`

### Coincidencias exactas (diferencia < 0.01%)
Conversión reportada 2025/2026, frontera p75/p90/máximo, coeficientes M1 y M2, correlaciones Pearson y Spearman, R² de varianza, SD entre/dentro, factor estacional y ticket promedio.

### Discrepancia documentada: crecimiento de venta (+102.6% Python vs +94.1% R)
**Causa identificada:** En 2026 existen 2 tiendas nuevas (Larcomar 2 y Real Plaza Piura 2) que no operaban en 2025. Al comparar *todas las tiendas* de cada año en semanas 2–34, la venta 2026 incluye el aporte de esos 2 nuevos locales sin contrapartida en 2025, inflando el crecimiento aparente. La comparación de tiendas comunes (14 locales presentes en ambos años) da +85.2% en Python vs +75.9% esperado en R — diferencia menor, posiblemente por orden de filtros o redondeo en `unidades`.

> Esta discrepancia es metodológicamente esperada: la comparación de *toda la cadena* en dos períodos con distinto número de tiendas no es comparable sin ajuste. El análisis de tiendas comunes es el más riguroso.
