# Análisis de horarios y headcount — The Box y Coolbrands

## Fuentes y alcance
- Archivo base: `Horarios_Headcount S34-S38.xlsx`
- Periodo confirmado: semanas ISO 34 a 38 de 2026 (2026-08-17 a 2026-09-20).
- Unidad de observación: cada turno programado en la hoja `BD`; cada fila representa una persona en una tienda, un día y un turno planificado.
- El campo `Cuenta` indica si la fila suma al head count. El archivo ya está filtrado a `Cuenta = Si` para la vista principal.
- Según `Notas`, la base representa horario planificado, no asistencia efectiva; se excluyen descansos, vacaciones, baja médica, ausencias y `TM` por inventario nocturno.

## Calidad de datos y exclusiones
- Registros totales: 3342.
- Registros incluidos (`Cuenta = Si`): 2592.
- Registros excluidos: 750.
- Descanso: 605 filas.
- Vacaciones: 91 filas.
- Descanso medico: 19 filas.
- Doble registro: estuvo en TB MGIND: 6 filas.
- Doble registro: estuvo en TB LMMIR 2: 6 filas.
- Doble registro: estuvo en TB RPCUS: 6 filas.
- Doble registro: estuvo en TB PCSI: 5 filas.
- Inventario nocturno (no es atencion): 4 filas.
- Doble registro: estuvo en TB RPPUR 1: 3 filas.
- Falta: 3 filas.
- Doble registro: estuvo en TB JPSU: 1 filas.
- Doble registro: estuvo en CB IOCA 1: 1 filas.

## Estadísticas clave del horario programado
- Personas distintas incluidas: 109 en 5 semanas.
- Turnos con duración >=11 horas: 19.0% del total de turnos.
- Horas programadas totales en la muestra: 23,436 horas-persona.
- La proporción de turnos largos sube de 4.7% en semana 34 a 33.1% en semana 38.

## Hallazgos relevantes
- El patrón dominante no es asistencia efectiva ni ventas; es cobertura programada, sin medición directa de presencia real.
- Las horas antes de las 09:30 se interpretan como apertura/despacho, no atención al público, según `Notas`.
- Los 28 casos de dobles registros quedaron resueltos con evidencia de ventas o continuidad, por lo que no se imputan de manera automática en la base principal.
- The Box tiene una estructura de turnos más larga a partir de la semana 36, con una expansión visible en la proporción de turnos de 11+ horas.

## Sugerencia para el paper
- Usar este análisis como evidencia descriptiva de la programación: la dotación se ajusta por semana, pero la base no permite atribuir causalidad ni déficit de personal sin un cruce con tráfico y una medición de asistencia efectiva.
- Para la redacción, evitar afirmar que ”la empresa nunca ajusta su programación” o que ”hay déficit de personal” solo por el número programado; lo defensible es que la cobertura varía por tienda y franja y que la proporción de turnos largos cambia de manera sostenida.

## Archivos generados
- `headcount_analysis.py`
- `outputs/tablas/headcount_summary.csv`
- `outputs/tablas/store_week_headcount.csv`
- `outputs/figuras/turnos_11mas_por_semana.png`
- `outputs/figuras/personas_dia_por_semana.png`
- `outputs/figuras/heatmap_personas_tienda_semana.png`

## Reproducibilidad
```bash
python analisis_horarios_headcount/headcount_analysis.py
```
