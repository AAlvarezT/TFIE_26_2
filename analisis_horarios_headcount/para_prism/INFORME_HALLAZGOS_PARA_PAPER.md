# Hallazgos para paper

## Resumen ejecutivo (resultados calculados)
- Fuente de horarios: `Horarios_Headcount S34-S38.xlsx`, hoja `BD`, con inclusión `Cuenta = Si`.
- Cobertura temporal horarios: semanas ISO 34 a 38 de 2026.
- Cobertura The Box para turnos largos: 16 tiendas.
- Cobertura total cadena para turnos largos: 19 tiendas (The Box + Coolbrands).
- Turnos largos (>=11h) en **The Box**:
  - Semana 34: 24/452 = 5.31%.
  - Semana 38: 161/406 = 39.66%.
- Turnos largos (>=11h) en **cadena total (19 tiendas)**:
  - Semana 34: 25/532 = 4.70%.
  - Semana 38: 164/496 = 33.06%.
- La reconstrucción por hora usa solapamiento semiabierto: turno `[ingreso, salida)` y franja `[hora, hora+1)`.
- El cruce comercial-horarios se limita a semana ISO 34 de 2026 para mantener un periodo común y auditable.

## Cruce con comercial (semana 34, The Box)
- Filas de ventas en población del cruce: 1361.
- Coincidencia encontrada: 1313.
- Cero confirmado (solo con respaldo horario del día): 48.
- Registro horario ausente: 0.
- Registro horario dudoso/no emparejado: 0.
- Anomalías de consistencia comercial: `transacciones > flujo` = 41; `flujo = 0` = 41.
- Advertencia metodológica: dotación programada no equivale a asistencia efectiva.

## Encuesta (BD NPS)
- Columna de calificación seleccionada explícitamente: `En una escala del 0 al 10, ¿qué tan buena fue la atención que recibiste hoy en nuestra tienda?`.
- Columna de comentario abierto seleccionada explícitamente: `¿Qué fue lo que más te gustó o qué podríamos mejorar?`.
- Registros NPS totales: 2781.
- Calificaciones válidas (0-10): 2781.
- Comentarios no vacíos: 2742.
- La clasificación separa **tema** y **valoración textual**. Una mención de precio/atención no se interpreta automáticamente como negativa.

## Qué sí y qué no interpretar
- Sí: cambios descriptivos en estructura de turnos y dotación programada por tienda/semana/franja.
- No: causalidad sobre conversión o satisfacción a partir de este paquete descriptivo.
- No: inferir asistencia efectiva de colaboradores ni opinión de toda la población de clientes.

## Párrafos propuestos para el paper
1. "En las semanas ISO 34-38 de 2026, la proporción de turnos de 11 o más horas en The Box (16 tiendas) aumentó de 5.31% (24/452) a 39.66% (161/406), medido sobre turnos programados con `Cuenta = Si`."
2. "En la cadena total (19 tiendas), los valores equivalentes fueron 4.70% en semana 34 y 33.06% en semana 38, por lo que cualquier comparación de marcas debe explicitar la población usada."
3. "El cruce horario-comercial de la semana 34 clasifica explícitamente coincidencias, ausencia de registro y ceros confirmados; por diseño, no interpreta dotación programada como presencia efectiva ni prueba causal de desempeño."
